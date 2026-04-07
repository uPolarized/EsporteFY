from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.forms import modelformset_factory
from django.contrib.contenttypes.models import ContentType
from .models import Partida, AvaliacaoQuadra, AvaliacaoJogador, PartidaRSVP
from .forms import PartidaForm, AvaliacaoQuadraForm, AvaliacaoJogadorForm
from quadras.models import Quadra
from social.models import Atividade
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST


# ---------------------------------------------------------
# ✅ CRIAR PARTIDA
# ---------------------------------------------------------
class CriarPartidaView(LoginRequiredMixin, CreateView):
    model = Partida
    form_class = PartidaForm
    template_name = 'partidas/criar_partida.html'
    success_url = reverse_lazy('feed')

    @transaction.atomic 
    def form_valid(self, form):
        form.instance.organizador = self.request.user
        messages.success(self.request, "Sua partida foi criada e já está visível para a comunidade.")
        
        # 1. O super().form_valid salva a partida no banco.
        # 2. O salvamento dispara o 'post_save' no signals.py.
        # 3. O signal cria a Atividade automaticamente.
        response = super().form_valid(form) 
        
        # Adiciona o organizador aos jogadores confirmados
        self.object.jogadores_confirmados.add(self.request.user)

        # --- REMOVIDO ---
        # A criação manual da atividade foi removida daqui para evitar duplicidade.
        # O signal já está fazendo esse trabalho.

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'redirect_url': str(self.get_success_url()),
                'partida_id': self.object.id,
                'message': 'Sua partida foi criada e já está visível para a comunidade.',
            })

        return response

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            error_messages = {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            }
            return JsonResponse({
                'status': 'error',
                'message': 'Não foi possível criar a partida.',
                'errors': error_messages,
            }, status=400)

        return super().form_invalid(form)

# ... (Mantenha o resto do arquivo igual, apenas a classe CriarPartidaView precisava de alteração) ...

# ---------------------------------------------------------
# ✅ Helper Nível de Habilidade
# ---------------------------------------------------------
def atende_nivel_minimo(user_nivel, nivel_minimo):
    if nivel_minimo == 'Qualquer':
        return True
    levels = ['Iniciante', 'Intermediario', 'Avancado', 'Competitivo']
    if user_nivel not in levels:
        return False
    return levels.index(user_nivel) >= levels.index(nivel_minimo)

# ---------------------------------------------------------
# ✅ FLUXO RSVP (Interesse -> Confirmar -> Recusar)
# ---------------------------------------------------------
@login_required
@require_POST
@transaction.atomic
def registrar_interesse_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    user = request.user

    if user == partida.organizador:
        messages.info(request, 'Você já organiza essa partida.')
        return redirect('feed')

    if not atende_nivel_minimo(user.perfil.nivel_habilidade, partida.nivel_minimo):
        # Abaixo do nível mínimo -> vai para "Aguardando Aprovação"
        novo_status = PartidaRSVP.STATUS_AGUARDANDO
        msg_sucesso = f'Sua solicitação de participação na partida "{partida.titulo}" foi enviada para aprovação do organizador.'
    else:
        # Nível igual ou superior -> entra direto ("Confirmado")
        novo_status = PartidaRSVP.STATUS_CONFIRMADO
        msg_sucesso = f'Sua presença está confirmada na partida "{partida.titulo}"!'

    if user in partida.jogadores_confirmados.all():
        messages.warning(request, "Você já está confirmado nesta partida.")
        return redirect('feed')

    if partida.vagas_restantes <= 0:
        messages.error(request, "Esta partida está lotada.")
        return redirect('feed')

    # Status existente
    rsvp, created = PartidaRSVP.objects.get_or_create(
        partida=partida,
        jogador=user,
        defaults={'status': novo_status}
    )

    if not created:
        if rsvp.status == novo_status:
            messages.info(request, f'Você já está registrado(a) com este status na partida "{partida.titulo}".')
            return redirect('feed')
            
        rsvp.status = novo_status
        rsvp.motivo_recusa = ''
        rsvp.observacao_recusa = ''
        rsvp.recusado_em = None
        if novo_status == PartidaRSVP.STATUS_CONFIRMADO:
            rsvp.confirmado_em = timezone.now()
        rsvp.save(update_fields=['status', 'motivo_recusa', 'observacao_recusa', 'recusado_em', 'confirmado_em', 'atualizado_em'])

    if novo_status == PartidaRSVP.STATUS_CONFIRMADO and not rsvp.confirmado_em:
        rsvp.confirmado_em = timezone.now()
        rsvp.save(update_fields=['confirmado_em', 'atualizado_em'])
        
    if novo_status == PartidaRSVP.STATUS_CONFIRMADO:
        partida.jogadores_confirmados.add(user)
    
    # Envia realtime manual apenas para solicitação pendente.
    # Quando o status é confirmado, o m2m_changed já notifica as duas contas.
    if novo_status == PartidaRSVP.STATUS_AGUARDANDO:
        try:
            from app.redis_utils import publish_to_redis
            
            remetente_nome = user.perfil.nome_exibicao if hasattr(user, 'perfil') and getattr(user.perfil, 'nome_exibicao', None) else user.username
            foto_url = user.perfil.foto.url if hasattr(user, 'perfil') and user.perfil.foto else '/static/images/default-avatar.png'
            mensagem = f'deseja participar da sua partida "{partida.titulo}" e aguarda sua aprovação.'

            payload_organizador = {
                'type': 'send_generic_notification',
                'titulo': 'Nova solicitação de participação',
                'remetente': remetente_nome,
                'mensagem': mensagem,
                'foto_url': foto_url,
                'notification_scope': 'user',
                'timestamp': 'agora',
                'timestamp_iso': timezone.now().isoformat(),
                'conversa_url': f'/partidas/{partida.id}/',
            }
            publish_to_redis(f'notifications_user_{partida.organizador.id}', payload_organizador)

            payload_solicitante = {
                'type': 'send_generic_notification',
                'titulo': 'Solicitação enviada',
                'remetente': 'Sistema EsporteFY',
                'mensagem': f'sua solicitação para "{partida.titulo}" foi enviada com sucesso.',
                'foto_url': '',
                'notification_scope': 'system',
                'transient_popup_only': True,
                'timestamp': 'agora',
                'timestamp_iso': timezone.now().isoformat(),
                'conversa_url': f'/partidas/{partida.id}/',
            }
            publish_to_redis(f'notifications_user_{user.id}', payload_solicitante)
        except Exception as e:
            print(f"Erro ao disparar socket de RSVP: {e}")

    messages.success(request, msg_sucesso)
    return redirect('feed')


@login_required
@require_POST
@transaction.atomic
def confirmar_presenca_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    user = request.user

    if user == partida.organizador:
        messages.info(request, 'Você já organiza essa partida.')
        return redirect('feed')

    if not atende_nivel_minimo(user.perfil.nivel_habilidade, partida.nivel_minimo):
        nivel_display = dict(Partida.NIVEL_MINIMO_CHOICES).get(partida.nivel_minimo, partida.nivel_minimo)
        messages.error(request, f"A partida requer um nível mínimo de habilidade: {nivel_display}.")
        return redirect('feed')

    if user in partida.jogadores_confirmados.all():
        PartidaRSVP.objects.update_or_create(
            partida=partida,
            jogador=user,
            defaults={
                'status': PartidaRSVP.STATUS_CONFIRMADO,
                'confirmado_em': timezone.now(),
                'motivo_recusa': '',
                'observacao_recusa': '',
                'recusado_em': None,
            },
        )
        messages.info(request, f'Você já está confirmado na partida "{partida.titulo}".')
        return redirect('feed')

    if partida.vagas_restantes <= 0:
        messages.error(request, 'Não foi possível confirmar: a partida está lotada.')
        return redirect('feed')

    PartidaRSVP.objects.update_or_create(
        partida=partida,
        jogador=user,
        defaults={
            'status': PartidaRSVP.STATUS_CONFIRMADO,
            'confirmado_em': timezone.now(),
            'motivo_recusa': '',
            'observacao_recusa': '',
            'recusado_em': None,
        },
    )

    partida.jogadores_confirmados.add(user)

    content_type = ContentType.objects.get_for_model(Partida)
    Atividade.objects.filter(
        ator=user,
        verbo__icontains='saiu',
        content_type=content_type,
        object_id=partida.id,
    ).delete()

    messages.success(request, f'Presença confirmada na partida "{partida.titulo}".')
    return redirect('feed')


@login_required
@require_POST
@transaction.atomic
def recusar_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    user = request.user

    if user == partida.organizador:
        messages.warning(request, 'Como organizador, você pode cancelar a partida em vez de recusar presença.')
        return redirect('feed')

    motivo = (request.POST.get('motivo_recusa') or '').strip() or 'Sem disponibilidade'
    observacao = (request.POST.get('observacao_recusa') or '').strip()

    PartidaRSVP.objects.update_or_create(
        partida=partida,
        jogador=user,
        defaults={
            'status': PartidaRSVP.STATUS_RECUSADO,
            'motivo_recusa': motivo[:255],
            'observacao_recusa': observacao,
            'recusado_em': timezone.now(),
        },
    )

    if user in partida.jogadores_confirmados.all():
        partida.jogadores_confirmados.remove(user)

    messages.info(request, f'Você marcou "Não vou" para a partida "{partida.titulo}".')
    return redirect('feed')


# Compatibilidade com rota antiga de participar.
@login_required
@require_POST
@transaction.atomic
def participar_partida(request, partida_id):
    return registrar_interesse_partida(request, partida_id)

# ---------------------------------------------------------
# ✅ APROVAR / RECUSAR JOGADOR (Organizador)
# ---------------------------------------------------------
@login_required
@require_POST
@transaction.atomic
def aprovar_jogador_partida(request, partida_id, jogador_id):
    """Organizador aprova um jogador que está 'Aguardando Aprovação'."""
    from django.contrib.auth.models import User
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    jogador = get_object_or_404(User, id=jogador_id)
    
    if request.user != partida.organizador:
        messages.error(request, 'Apenas o organizador pode aprovar jogadores.')
        return redirect('feed')
    
    rsvp = get_object_or_404(PartidaRSVP, partida=partida, jogador=jogador)
    
    if rsvp.status == PartidaRSVP.STATUS_CONFIRMADO:
        messages.info(request, f'{jogador.username} já está confirmado.')
        return redirect('feed')
    
    if partida.vagas_restantes <= 0:
        messages.error(request, 'Não há vagas disponíveis.')
        return redirect('feed')
    
    rsvp.status = PartidaRSVP.STATUS_CONFIRMADO
    rsvp.confirmado_em = timezone.now()
    rsvp.motivo_recusa = ''
    rsvp.observacao_recusa = ''
    rsvp.recusado_em = None
    rsvp.save()
    
    partida.jogadores_confirmados.add(jogador)
    
    # Notificar jogador aprovado
    try:
        from app.redis_utils import publish_to_redis
        foto_url = request.user.perfil.foto.url if hasattr(request.user, 'perfil') and request.user.perfil.foto else ''
        payload = {
            'type': 'send_generic_notification',
            'remetente': 'Organizador',
            'mensagem': f'aprovou sua participação na partida "{partida.titulo}".',
            'foto_url': foto_url,
            'timestamp': 'agora',
            'conversa_url': f'/partidas/{partida.id}/' 
        }
        publish_to_redis(f'notifications_user_{jogador.id}', payload)
    except Exception:
        pass

    messages.success(request, f'{jogador.username} foi aprovado(a) para a partida.')
    return redirect(request.META.get('HTTP_REFERER', 'feed'))


@login_required
@require_POST
@transaction.atomic
def recusar_jogador_partida(request, partida_id, jogador_id):
    """Organizador recusa um jogador que está 'Aguardando Aprovação'."""
    from django.contrib.auth.models import User
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    jogador = get_object_or_404(User, id=jogador_id)
    
    if request.user != partida.organizador:
        messages.error(request, 'Apenas o organizador pode recusar jogadores.')
        return redirect('feed')
    
    rsvp = get_object_or_404(PartidaRSVP, partida=partida, jogador=jogador)
    
    rsvp.status = PartidaRSVP.STATUS_RECUSADO
    rsvp.motivo_recusa = 'Recusado pelo organizador'
    rsvp.recusado_em = timezone.now()
    rsvp.save()
    
    if jogador in partida.jogadores_confirmados.all():
        partida.jogadores_confirmados.remove(jogador)

    # Notificar jogador recusado
    try:
        from app.redis_utils import publish_to_redis
        foto_url = request.user.perfil.foto.url if hasattr(request.user, 'perfil') and request.user.perfil.foto else ''
        payload = {
            'type': 'send_generic_notification',
            'remetente': 'Organizador',
            'mensagem': f'recusou sua solicitação na partida "{partida.titulo}".',
            'foto_url': foto_url,
            'timestamp': 'agora',
            'conversa_url': f'/partidas/{partida.id}/' 
        }
        publish_to_redis(f'notifications_user_{jogador.id}', payload)
    except Exception:
        pass
    
    messages.info(request, f'{jogador.username} foi recusado(a) na partida.')
    return redirect(request.META.get('HTTP_REFERER', 'feed'))

# ... (Mantenha o resto do arquivo como estava) ...
@login_required
@require_POST
@transaction.atomic
def sair_da_partida(request, partida_id):
    # Busca otimizada da partida
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    user = request.user

    # Organizador não pode sair
    if user == partida.organizador:
        messages.error(
            request,
            'Você é o organizador e não pode sair da partida. Se necessário, cancele a partida.'
        )
        return redirect('feed')

    # Se o usuário está participando
    if user in partida.jogadores_confirmados.all():
        partida.jogadores_confirmados.remove(user)

        content_type = ContentType.objects.get_for_model(Partida)

        # 🧹 Remove atividades antigas de "entrou" e "saiu" relacionadas a essa partida
        Atividade.objects.filter(
            ator=user,
            content_type=content_type,
            object_id=partida.id
        ).filter(verbo__icontains="entrou").delete()

        messages.info(request, f'Você saiu da partida "{partida.titulo}".')

    else:
        messages.warning(request, 'Você não estava nesta partida.')

    return redirect('feed')

@login_required
@require_POST
@transaction.atomic
def cancelar_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id, organizador=request.user)

    # Referência ao tipo do objeto Partida
    content_type = ContentType.objects.get_for_model(partida)

    # 1️⃣ APAGAR TODAS AS ATIVIDADES RELACIONADAS A ESSA PARTIDA
    Atividade.objects.filter(
        content_type=content_type,
        object_id=partida.id
    ).delete()

    # 2️⃣ APAGAR A PRÓPRIA PARTIDA
    partida.delete()

    messages.success(request, "Partida cancelada com sucesso.")
    return redirect("partidas:minhas_partidas")


    # 🔥 Agora sim cancelando de verdade!
    partida.delete()

    messages.success(request, "Partida cancelada com sucesso!")
    return redirect('partidas:minhas_partidas')


    partida.delete()
    messages.success(request, "A partida foi cancelada com sucesso!")

    return redirect('feed')

class MinhasPartidasView(LoginRequiredMixin, ListView):
    model = Partida
    template_name = 'partidas/minhas_partidas.html'
    context_object_name = 'partidas'

    def get_queryset(self):
        return (
            self.request.user.partidas_confirmadas.all()
            .order_by('-data_hora')
            .select_related('quadra')
            .prefetch_related('jogadores_confirmados')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        todas_as_partidas = context['partidas']

        avaliacoes = AvaliacaoQuadra.objects.filter(
            avaliador=self.request.user,
            partida__in=todas_as_partidas
        ).values_list('partida_id', flat=True)
        partidas_avaliadas_ids = set(avaliacoes)

        partidas_futuras, partidas_passadas = [], []
        for p in todas_as_partidas:
            p.avaliada = p.id in partidas_avaliadas_ids 
            if p.data_hora >= now:
                partidas_futuras.append(p)
            else:
                partidas_passadas.append(p)

        context['partidas_futuras'] = partidas_futuras
        context['partidas_passadas'] = partidas_passadas
        del context['partidas'] 

        return context

@login_required
@transaction.atomic
def avaliar_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.prefetch_related('jogadores_confirmados__perfil'), 
        id=partida_id
    )
    avaliador = request.user

    if AvaliacaoQuadra.objects.filter(partida=partida, avaliador=avaliador).exists():
        messages.warning(request, "Você já avaliou esta partida.")
        return redirect('partidas:minhas_partidas')

    outros_jogadores = [j for j in partida.jogadores_confirmados.all() if j.id != avaliador.id]
    AvaliacaoJogadorFormSet = modelformset_factory(AvaliacaoJogador, form=AvaliacaoJogadorForm, extra=len(outros_jogadores))

    if request.method == 'POST':
        quadra_form = AvaliacaoQuadraForm(request.POST)
        jogador_formset = AvaliacaoJogadorFormSet(request.POST)

        if quadra_form.is_valid() and jogador_formset.is_valid():
            avaliacao_quadra = quadra_form.save(commit=False)
            avaliacao_quadra.partida = partida
            avaliacao_quadra.avaliador = avaliador
            avaliacao_quadra.save()

            for i, form in enumerate(jogador_formset):
                if form.cleaned_data:
                    avaliacao_jogador = form.save(commit=False)
                    avaliacao_jogador.partida = partida
                    avaliacao_jogador.avaliador = avaliador
                    avaliacao_jogador.avaliado = outros_jogadores[i]
                    avaliacao_jogador.save()

            content_type = ContentType.objects.get_for_model(partida)
            Atividade.objects.update_or_create(
                ator=request.user,
                verbo='avaliou',
                content_type=content_type,
                object_id=partida.id,
                defaults={}
            )

            messages.success(request, "Obrigado pela sua avaliação!")
            return redirect('partidas:minhas_partidas')

    else:
        quadra_form = AvaliacaoQuadraForm()
        jogador_formset = AvaliacaoJogadorFormSet(queryset=AvaliacaoJogador.objects.none())

    forms_e_jogadores = zip(jogador_formset.forms, outros_jogadores)

    context = {
        'partida': partida,
        'quadra_form': quadra_form,
        'jogador_formset': jogador_formset,
        'forms_e_jogadores': forms_e_jogadores,
    }
    return render(request, 'partidas/avaliar_partida.html', context)

@login_required
@require_GET
def partidas_statuses(request):
    ids = request.GET.get('ids', '')
    if not ids:
        return JsonResponse({}, status=200)

    try:
        ids_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
    except ValueError:
        return JsonResponse({}, status=400)

    usuario = request.user
    avaliacoes = AvaliacaoQuadra.objects.filter(partida_id__in=ids_list, avaliador=usuario).values_list('partida_id', flat=True)
    avaliadas_set = set(avaliacoes)

    result = {}
    for pid in ids_list:
        result[str(pid)] = {'avaliada': pid in avaliadas_set}

    return JsonResponse(result)


@require_GET
def api_esportes(request):
    try:
        from .models import Esporte
        esportes = Esporte.objects.all().order_by('nome')
        data = [{'id': e.id, 'nome': e.nome, 'icone': getattr(e, 'icone', '')} for e in esportes]
        return JsonResponse({'esportes': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

