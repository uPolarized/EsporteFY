from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db import models
from django.db.models import Q, Count
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils import timezone
from allauth.account.views import PasswordSetView

from app.redis_utils import publish_to_redis, is_user_online, get_user_last_seen, list_online_user_ids

from .models import Perfil, SolicitacaoAmizade, UserPrivacySettings, AccountLoginEvent
from .forms import PerfilForm, FiltroUsuarioForm
from partidas.models import Partida
from partidas.finalizacao import processar_partidas_finalizadas
from .forms import SetPasswordCaptchaForm
from social.models import Atividade
from social.security import throttle_request


def _exclude_friendship_activities(queryset):
    return queryset.exclude(
        Q(verbo__icontains='agora são amigos') |
        Q(verbo__icontains='agora sao amigos')
    )


def _format_last_seen_label(dt):
    if not dt:
        return 'Sem registro recente'

    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    local_dt = timezone.localtime(dt)
    delta = now - dt
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        return 'Agora mesmo'

    if total_seconds < 60:
        return 'Agora mesmo'

    if total_seconds < 3600:
        minutes = max(1, total_seconds // 60)
        unit = 'minuto' if minutes == 1 else 'minutos'
        return f'Ha {minutes} {unit}'

    if total_seconds < 86400:
        hours = max(1, total_seconds // 3600)
        unit = 'hora' if hours == 1 else 'horas'
        return f'Ha {hours} {unit}'

    if local_dt.date() == timezone.localdate():
        return f'Hoje as {local_dt:%H:%M}'

    if local_dt.date() == timezone.localdate() - timedelta(days=1):
        return f'Ontem as {local_dt:%H:%M}'

    if total_seconds < 7 * 86400:
        weekdays = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        weekday = weekdays[local_dt.weekday()]
        return f'{weekday} as {local_dt:%H:%M}'

    return local_dt.strftime('%d/%m/%Y as %H:%M')


# ============================================================
# LISTAGEM DE USUÁRIOS
# ============================================================
class ListaUsuariosView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'perfis/lista_usuarios.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).select_related('perfil')
        form = FiltroUsuarioForm(self.request.GET)

        if form.is_valid():
            nome   = form.cleaned_data.get('nome_usuario')
            esporte = form.cleaned_data.get('esporte')
            nivel  = form.cleaned_data.get('nivel')
            bairro = form.cleaned_data.get('bairro')

            if nome:
                queryset = queryset.filter(username__icontains=nome)
            if esporte:
                queryset = queryset.filter(perfil__esportes_preferidos=esporte)
            if nivel:
                queryset = queryset.filter(perfil__nivel_habilidade=nivel)
            if bairro:
                queryset = queryset.filter(perfil__bairro_base=bairro)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['filtro_form'] = FiltroUsuarioForm(self.request.GET or None)

        amigos = user.perfil.amigos.all()
        solicitacoes_enviadas_qs  = SolicitacaoAmizade.objects.filter(solicitante=user)
        solicitacoes_recebidas_qs = SolicitacaoAmizade.objects.filter(receptor=user)

        context['amigos_lista']   = list(amigos)
        context['enviadas_lista'] = [s.receptor   for s in solicitacoes_enviadas_qs]
        context['recebidas_lista'] = [s.solicitante for s in solicitacoes_recebidas_qs]

        context['sidebar_total_jogadores'] = User.objects.exclude(id=user.id).count()
        context['sidebar_total_amigos'] = amigos.count()
        context['sidebar_solicitacoes_pendentes'] = solicitacoes_recebidas_qs.count()

        bairros_populares = (
            Perfil.objects.exclude(bairro_base__isnull=True)
            .exclude(bairro_base='')
            .values('bairro_base')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )
        context['sidebar_bairros_populares'] = list(bairros_populares)

        return context


# ============================================================
# SOLICITAÇÕES DE AMIZADE
# ============================================================
@login_required
@require_POST
def enviar_solicitacao_amizade(request, receptor_id):
    allowed, _ = throttle_request(request, scope='friend_request', limit=20, window_seconds=3600)
    if not allowed:
        messages.error(request, 'Muitas solicitações de amizade em pouco tempo. Tente novamente mais tarde.')
        return redirect('perfis:lista_usuarios')

    receptor   = get_object_or_404(User, id=receptor_id)
    solicitante = request.user

    if receptor.id == solicitante.id:
        messages.warning(request, 'Você não pode enviar solicitação para si mesmo.')
        return redirect('perfis:lista_usuarios')

    if hasattr(receptor, 'privacy_settings') and not receptor.privacy_settings.allow_friend_requests:
        messages.info(request, f'{receptor.username} desativou novas solicitações de amizade no momento.')
        return redirect('perfis:lista_usuarios')

    if solicitante.perfil.amigos.filter(id=receptor.id).exists():
        messages.info(request, f'Você já é amigo(a) de {receptor.username}.')
        return redirect('perfis:lista_usuarios')

    ja_existe = (
        SolicitacaoAmizade.objects.filter(solicitante=solicitante, receptor=receptor).exists() or
        SolicitacaoAmizade.objects.filter(solicitante=receptor,   receptor=solicitante).exists()
    )

    if not ja_existe:
        solicitacao = SolicitacaoAmizade.objects.create(
            solicitante=solicitante, receptor=receptor
        )
        publish_to_redis(
            f"notifications_user_{receptor.id}",
            {
                "type": "send_generic_notification",
                "mensagem": f"{solicitante.username} enviou uma solicitação de amizade.",
            },
        )
        messages.success(request, f'Pedido de amizade enviado para {receptor.username}.')
    else:
        messages.warning(request, f'Já existe uma solicitação ou amizade com {receptor.username}.')

    return redirect('perfis:lista_usuarios')


@login_required
@require_POST
def aceitar_solicitacao(request, solicitacao_id):
    allowed, _ = throttle_request(request, scope='friend_request_accept', limit=40, window_seconds=60)
    if not allowed:
        messages.error(request, 'Muitas ações em pouco tempo. Tente novamente em instantes.')
        return redirect('perfis:meu_perfil')

    solicitacao = SolicitacaoAmizade.objects.filter(id=solicitacao_id, receptor=request.user).select_related('solicitante', 'receptor').first()
    if not solicitacao:
        # Resposta genérica para reduzir enumeração de IDs.
        messages.info(request, 'Solicitação indisponível ou já processada.')
        return redirect('perfis:meu_perfil')

    solicitacao.receptor.perfil.amigos.add(solicitacao.solicitante)
    solicitacao.solicitante.perfil.amigos.add(solicitacao.receptor)
    solicitante = solicitacao.solicitante
    solicitacao.delete()

    publish_to_redis(
        f"notifications_user_{solicitante.id}",
        {
            "type": "notification",
            "remetente": request.user.username,
                "mensagem": "aceitou sua solicitação de amizade.",
                "conversa_url": f"/perfis/usuario/{request.user.username}/",
            "timestamp": "agora",
        },
    )

    messages.success(request, f"Você e {solicitante.username} agora são amigos!")

    return redirect('perfis:meu_perfil')


@login_required
@require_POST
def recusar_solicitacao(request, solicitacao_id):
    allowed, _ = throttle_request(request, scope='friend_request_reject', limit=40, window_seconds=60)
    if not allowed:
        messages.error(request, 'Muitas ações em pouco tempo. Tente novamente em instantes.')
        return redirect('perfis:meu_perfil')

    solicitacao = SolicitacaoAmizade.objects.filter(id=solicitacao_id, receptor=request.user).select_related('solicitante').first()
    if not solicitacao:
        # Resposta genérica para reduzir enumeração de IDs.
        messages.info(request, 'Solicitação indisponível ou já processada.')
        return redirect('perfis:meu_perfil')

    solicitante = solicitacao.solicitante
    solicitacao.delete()

    messages.info(request, f"Pedido de amizade de {solicitante.username} recusado.")

    return redirect('perfis:meu_perfil')


@login_required
@require_POST
def remover_amigo(request, user_id):
    allowed, _ = throttle_request(request, scope='friend_remove', limit=30, window_seconds=60)
    if not allowed:
        messages.error(request, 'Muitas ações em pouco tempo. Tente novamente em instantes.')
        return redirect('perfis:meu_perfil')

    amigo_a_remover = get_object_or_404(User, id=user_id)
    usuario_logado  = request.user

    if amigo_a_remover.id == usuario_logado.id:
        messages.warning(request, 'Ação inválida.')
        return redirect('perfis:meu_perfil')

    if not usuario_logado.perfil.amigos.filter(id=amigo_a_remover.id).exists():
        messages.info(request, 'Este usuário já não está na sua lista de amigos.')
        return redirect('perfis:ver_perfil', username=amigo_a_remover.username)

    usuario_logado.perfil.amigos.remove(amigo_a_remover)
    amigo_a_remover.perfil.amigos.remove(usuario_logado)

    messages.info(request, f"Você não é mais amigo(a) de {amigo_a_remover.username}.")
    return redirect('perfis:ver_perfil', username=amigo_a_remover.username)


@login_required
@require_POST
def toggle_online_status(request):
    privacy, _ = UserPrivacySettings.objects.get_or_create(user=request.user)
    privacy.show_online_status = not privacy.show_online_status
    privacy.save(update_fields=['show_online_status', 'updated_at'])

    status_label = 'visível' if privacy.show_online_status else 'oculto'
    messages.success(request, f'Seu status online agora está {status_label}.')

    return redirect(request.META.get('HTTP_REFERER', 'feed'))


# ============================================================
# PERFIL DO USUÁRIO LOGADO
# ============================================================
class MeuPerfilView(LoginRequiredMixin, DetailView):
    model = Perfil
    template_name = 'perfis/meu_perfil.html'
    context_object_name = 'object'

    def get_object(self):
        return self.request.user.perfil

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil_logado = self.object
        user_logado   = perfil_logado.user

        from django.utils import timezone

        context['solicitacoes_pendentes'] = SolicitacaoAmizade.objects.filter(
            receptor=self.request.user, aceito=False
        )
        context['total_amigos']   = perfil_logado.amigos.count()
        context['total_partidas'] = Partida.objects.filter(
            jogadores_confirmados=perfil_logado.user
        ).count()

        todos_amigos    = list(perfil_logado.amigos.all())
        amigos_com_info = []

        for amigo in todos_amigos:
            try:
                solicitacao = SolicitacaoAmizade.objects.filter(
                    models.Q(solicitante=user_logado, receptor=amigo) |
                    models.Q(solicitante=amigo, receptor=user_logado)
                ).first()

                dias_amigo = (timezone.now() - solicitacao.timestamp).days if solicitacao else 0

                amigos_do_amigo  = set(amigo.perfil.amigos.all())
                amigos_do_usuario = set(perfil_logado.amigos.all())
                amigos_comuns    = len(amigos_do_amigo & amigos_do_usuario)

                partidas_amigo   = set(Partida.objects.filter(jogadores_confirmados=amigo).values_list('id', flat=True))
                partidas_usuario = set(Partida.objects.filter(jogadores_confirmados=user_logado).values_list('id', flat=True))
                partidas_comuns  = len(partidas_amigo & partidas_usuario)

                is_online    = is_user_online(amigo.id)
                perfil_amigo = amigo.perfil
                nivel        = getattr(perfil_amigo, 'nivel', 'Iniciante')
                esporte      = getattr(perfil_amigo, 'esporte_favorito', 'Não especificado')

                amigos_com_info.append({
                    'amigo': amigo,
                    'dias': dias_amigo,
                    'amigos_comuns': amigos_comuns,
                    'partidas_comuns': partidas_comuns,
                    'is_online': is_online,
                    'nivel': nivel,
                    'esporte': esporte,
                })
            except Exception:
                amigos_com_info.append({
                    'amigo': amigo,
                    'dias': 0,
                    'amigos_comuns': 0,
                    'partidas_comuns': 0,
                    'is_online': False,
                    'nivel': 'Sem info',
                    'esporte': 'Sem info',
                })

        context['amigos_recentes'] = amigos_com_info[:8]
        context['amigos_com_info'] = amigos_com_info
        context['giphy_api_key'] = getattr(settings, 'GIPHY_API_KEY', 'dc6zaTOxFJmzC')

        return context


# ============================================================
# VISUALIZAR PERFIL DE OUTROS USUÁRIOS
# ============================================================
class VerPerfilView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'perfis/ver_perfil.html'
    context_object_name = 'object'
    slug_field    = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_logado           = self.request.user
        perfil_visitado_user  = self.get_object()
        perfil_visitado_perfil = perfil_visitado_user.perfil

        context['ja_sao_amigos'] = user_logado.perfil.amigos.filter(
            id=perfil_visitado_user.id
        ).exists()
        context['pedido_enviado'] = SolicitacaoAmizade.objects.filter(
            solicitante=user_logado, receptor=perfil_visitado_user
        ).exists()
        context['pedido_recebido'] = SolicitacaoAmizade.objects.filter(
            solicitante=perfil_visitado_user, receptor=user_logado
        ).exists()
        context['total_amigos']   = perfil_visitado_perfil.amigos.count()
        context['total_partidas'] = Partida.objects.filter(
            jogadores_confirmados=perfil_visitado_user
        ).count()

        # Preparar informações de amigos para sidebar e status online
        from django.utils import timezone

        todos_amigos = list(perfil_visitado_perfil.amigos.all())
        amigos_com_info = []

        for amigo in todos_amigos:
            try:
                solicitacao = SolicitacaoAmizade.objects.filter(
                    models.Q(solicitante=user_logado, receptor=amigo) |
                    models.Q(solicitante=amigo, receptor=user_logado)
                ).first()

                dias_amigo = (timezone.now() - solicitacao.timestamp).days if solicitacao else 0

                amigos_do_amigo = set(amigo.perfil.amigos.all())
                amigos_do_usuario = set(perfil_visitado_perfil.amigos.all())
                amigos_comuns = len(amigos_do_amigo & amigos_do_usuario)

                partidas_amigo = set(Partida.objects.filter(jogadores_confirmados=amigo).values_list('id', flat=True))
                partidas_usuario = set(Partida.objects.filter(jogadores_confirmados=perfil_visitado_user).values_list('id', flat=True))
                partidas_comuns = len(partidas_amigo & partidas_usuario)

                is_online = is_user_online(amigo.id)
                perfil_amigo = amigo.perfil
                nivel = getattr(perfil_amigo, 'nivel', 'Iniciante')
                esporte = getattr(perfil_amigo, 'esporte_favorito', 'Não especificado')

                amigos_com_info.append({
                    'amigo': amigo,
                    'dias': dias_amigo,
                    'amigos_comuns': amigos_comuns,
                    'partidas_comuns': partidas_comuns,
                    'is_online': is_online,
                    'nivel': nivel,
                    'esporte': esporte,
                })
            except Exception:
                amigos_com_info.append({
                    'amigo': amigo,
                    'dias': 0,
                    'amigos_comuns': 0,
                    'partidas_comuns': 0,
                    'is_online': False,
                    'nivel': 'Sem info',
                    'esporte': 'Sem info',
                })

        context['amigos_recentes'] = amigos_com_info[:8]
        context['amigos_com_info'] = amigos_com_info
        context['giphy_api_key'] = getattr(settings, 'GIPHY_API_KEY', 'dc6zaTOxFJmzC')

        return context


# ============================================================
# EDITAR PERFIL
# ============================================================
class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model      = Perfil
    form_class = PerfilForm
    template_name = 'perfis/editar_perfil.html'
    success_url   = reverse_lazy('perfis:meu_perfil')

    def get_object(self):
        return self.request.user.perfil

    def form_valid(self, form):
        import os
        from django.conf import settings
        from social.utils.image_moderation import analisar_imagem

        perfil_atual = self.get_object()

        # ── Snapshot antes de salvar ────────────────────────
        old_foto_name   = perfil_atual.foto.name   if perfil_atual.foto   else None
        old_banner_name = perfil_atual.banner.name if perfil_atual.banner else None

        removeu_foto   = self.request.POST.get('foto-clear')   == 'true'
        removeu_banner = self.request.POST.get('banner-clear') == 'true'

        tem_nova_foto   = bool(form.cleaned_data.get('foto')   and hasattr(form.cleaned_data['foto'],   'file'))
        tem_novo_banner = bool(form.cleaned_data.get('banner') and hasattr(form.cleaned_data['banner'], 'file'))

        # ── Salva tudo no banco/disco ───────────────────────
        response = super().form_valid(form)
        perfil   = self.object  # instância já salva

        # ── Remoção de foto ─────────────────────────────────
        if removeu_foto:
            perfil.foto = 'fotos_perfil/default.jpg'
            perfil.save(update_fields=['foto'])
            messages.success(self.request, "✅ Foto removida. Avatar padrão restaurado.")
            return response

        # ── Remoção de banner ───────────────────────────────
        if removeu_banner:
            if old_banner_name:
                old_path = os.path.join(settings.MEDIA_ROOT, old_banner_name)
                if os.path.exists(old_path):
                    os.remove(old_path)
            perfil.banner = None
            perfil.save(update_fields=['banner'])
            messages.success(self.request, "✅ Banner removido.")
            return response

        # ── Moderação de foto nova ──────────────────────────
        if tem_nova_foto:
            try:
                foto_path = perfil.foto.path
                is_safe, details = analisar_imagem(foto_path)
                if not is_safe:
                    if os.path.exists(foto_path):
                        os.remove(foto_path)
                    perfil.foto = old_foto_name or 'fotos_perfil/default.jpg'
                    perfil.save(update_fields=['foto'])
                    messages.error(
                        self.request,
                        "❌ Sua foto foi recusada por conter conteúdo inapropriado."
                    )
                    return redirect(reverse('perfis:editar_perfil'))
            except Exception as e:
                print(f"⚠️ Erro na moderação (foto): {e}")

        # ── Moderação de banner novo ────────────────────────
        if tem_novo_banner:
            try:
                banner_path = perfil.banner.path
                is_safe, details = analisar_imagem(banner_path)
                if not is_safe:
                    if os.path.exists(banner_path):
                        os.remove(banner_path)
                    perfil.banner = old_banner_name  # None ou o anterior
                    perfil.save(update_fields=['banner'])
                    messages.error(
                        self.request,
                        "❌ Seu banner foi recusado por conter conteúdo inapropriado."
                    )
                    return redirect(reverse('perfis:editar_perfil'))
            except Exception as e:
                print(f"⚠️ Erro na moderação (banner): {e}")

        # ── Posição do banner (vem do JS via campo hidden) ──
        # O form já salva banner_position automaticamente,
        # mas garantimos caso o campo hidden não esteja no form_class
        banner_position = self.request.POST.get('banner_position', '').strip()
        if banner_position:
            perfil.banner_position = banner_position
            perfil.save(update_fields=['banner_position'])

        messages.success(self.request, "✅ Perfil atualizado com sucesso!")
        return response


# ============================================================
# CUSTOM PASSWORD SET (Allauth)
# ============================================================
class CustomPasswordSetView(PasswordSetView):
    form_class = SetPasswordCaptchaForm

    def form_valid(self, form):
        if not form.cleaned_data.get('captcha'):
            messages.error(self.request, "⚠️ Verificação reCAPTCHA falhou. Tente novamente.")
            return self.form_invalid(form)
        return super().form_valid(form)


# ============================================================
# API DE STATUS ONLINE (POLLING A CADA 15s)
# ============================================================
@login_required
def api_check_status(request):
    allowed, _ = throttle_request(request, scope='api_check_status', limit=60, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em instantes.'}, status=429)

    ids_param = request.GET.get('ids', '')
    ids = [i for i in ids_param.split(',') if i.isdigit()][:100]

    allowed_ids = set(str(uid) for uid in request.user.perfil.amigos.values_list('id', flat=True))
    allowed_ids.add(str(request.user.id))

    filtered_ids = [uid for uid in ids if uid in allowed_ids]
    status_data = {user_id: is_user_online(user_id) for user_id in filtered_ids}
    return JsonResponse(status_data)


@login_required
def api_atividades(request):
    allowed, _ = throttle_request(request, scope='api_atividades', limit=30, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em instantes.'}, status=429)

    processar_partidas_finalizadas()

    user_id = request.GET.get('user_id')

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'page inválida'}, status=400)

    try:
        page_size = min(20, max(1, int(request.GET.get('page_size', 8))))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'page_size inválido'}, status=400)

    if not user_id or not user_id.isdigit():
        return JsonResponse({'error': 'user_id inválido'}, status=400)

    user = get_object_or_404(User, id=user_id)
    if user.id != request.user.id and not request.user.perfil.amigos.filter(id=user.id).exists() and not request.user.is_staff:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    atividades = _exclude_friendship_activities(
        Atividade.objects.filter(ator=user).select_related('content_type')
    ).order_by('-timestamp')
    total = atividades.count()

    start = (page - 1) * page_size
    end = start + page_size
    items = []

    for a in atividades[start:end]:
        obj = a.get_objeto()
        quadra = getattr(obj, 'quadra', None)

        quadra_foto_url = None
        if quadra:
            foto = quadra.fotos.first()
            if foto:
                quadra_foto_url = foto.imagem.url

        titulo_obj = getattr(obj, 'titulo', '') if obj else ''

        items.append({
            'id': a.id,
            'verbo': a.verbo,
            'descricao': a.get_descricao_formatada(),
            'timestamp': a.timestamp.strftime('%d/%m/%Y %H:%M'),
            'titulo': titulo_obj,
            'quadra_nome': getattr(quadra, 'nome', None),
            'quadra_bairro': getattr(quadra, 'get_bairro_display', lambda: None)() if quadra else None,
            'quadra_foto_url': quadra_foto_url,
        })

    return JsonResponse({
        'page': page,
        'page_size': page_size,
        'total': total,
        'activities': items,
    })


@login_required
def api_solicitacoes_amizade(request):
    """
    Retorna notificações de amizade pendentes recebidas do usuário logado.
    """
    allowed, _ = throttle_request(request, scope='api_solicitacoes_amizade', limit=60, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em instantes.'}, status=429)

    user = request.user

    # Solicitações recebidas
    recebidas = SolicitacaoAmizade.objects.filter(
        receptor=user
    ).select_related('solicitante', 'solicitante__perfil').order_by('-timestamp')

    recebidas_data = []
    for s in recebidas:
        recebidas_data.append({
            'id': s.id,
            'usuario_id': s.solicitante.id,
            'username': s.solicitante.username,
            'foto_url': s.solicitante.perfil.foto.url if s.solicitante.perfil.foto else '/media/fotos_perfil/default.jpg',
            'tipo': 'recebida',
            'timestamp': s.timestamp.isoformat(),
        })

    return JsonResponse({
        'recebidas': recebidas_data,
        'total': len(recebidas_data),
    })


@login_required
def api_perfil(request, user_id):
    allowed, _ = throttle_request(request, scope='api_perfil_modal', limit=60, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em instantes.'}, status=429)

    alvo = get_object_or_404(User.objects.select_related('perfil'), id=user_id)
    viewer = request.user

    ja_sao_amigos = viewer.perfil.amigos.filter(id=alvo.id).exists()
    has_request = SolicitacaoAmizade.objects.filter(solicitante=viewer, receptor=alvo).exists()

    privacy = getattr(alvo, 'privacy_settings', None)
    show_online_status = getattr(privacy, 'show_online_status', True)
    allow_friend_requests = getattr(privacy, 'allow_friend_requests', True)

    is_online = bool(is_user_online(alvo.id)) if show_online_status else False
    last_seen_dt = get_user_last_seen(alvo.id) or alvo.last_login

    response = {
        'user': {
            'id': alvo.id,
            'username': alvo.username,
        },
        'foto': alvo.perfil.foto.url if alvo.perfil.foto else '',
        'banner': alvo.perfil.banner.url if getattr(alvo.perfil, 'banner', None) else '',
        'mini_bio': alvo.perfil.mini_bio if getattr(alvo.perfil, 'mini_bio', None) else '',
        'esporte': getattr(alvo.perfil, 'esportes_preferidos', '') or 'Não informado',
        'nivel': getattr(alvo.perfil, 'nivel_habilidade', '') or 'Não informado',
        'cidade': getattr(alvo.perfil, 'cidade', '') or '',
        'bairro': alvo.perfil.get_bairro_base_display() if getattr(alvo.perfil, 'bairro_base', None) else '',
        'member_since': alvo.date_joined.strftime('%m/%Y') if getattr(alvo, 'date_joined', None) else '—',
        'partidas_count': Partida.objects.filter(jogadores_confirmados=alvo).count(),
        'amigos_count': alvo.perfil.amigos.count(),
        'rating': getattr(alvo.perfil, 'rating', None),
        'is_friend': ja_sao_amigos,
        'has_request': has_request,
        'allow_friend_requests': allow_friend_requests,
        'show_online_status': show_online_status,
        'is_online': is_online,
        'last_seen_at': last_seen_dt.isoformat() if last_seen_dt else None,
        'last_seen_label': _format_last_seen_label(last_seen_dt),
    }

    return JsonResponse(response)


@login_required
def api_online_players(request):
    allowed, _ = throttle_request(request, scope='api_online_players', limit=60, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em instantes.'}, status=429)

    q = (request.GET.get('q') or '').strip()
    try:
        limit = int(request.GET.get('limit', 14))
    except (TypeError, ValueError):
        limit = 14
    limit = max(1, min(limit, 40))

    online_ids = list_online_user_ids(max_items=500)
    online_id_set = set(online_ids)
    self_online = bool(is_user_online(request.user.id) or is_user_online(request.user.username))

    queryset = User.objects.filter(id__in=online_ids).exclude(id=request.user.id).select_related('perfil')
    if q:
        queryset = queryset.filter(username__icontains=q)

    online_by_id = {u.id: u for u in queryset}

    # Fallback 1: sem presença no Redis, usa eventos de login (inclui social login).
    if not online_by_id:
        recent_login_threshold = timezone.now() - timedelta(hours=24)
        recent_login_ids = list(
            AccountLoginEvent.objects
            .filter(created_at__gte=recent_login_threshold)
            .order_by('-created_at')
            .values_list('user_id', flat=True)
            .distinct()[:500]
        )

        recent_qs = User.objects.filter(id__in=recent_login_ids).exclude(id=request.user.id).select_related('perfil')
        if q:
            recent_qs = recent_qs.filter(username__icontains=q)

        # Fallback 2: se não houver eventos, usa last_login recente.
        if not recent_qs.exists():
            recent_threshold = timezone.now() - timedelta(minutes=30)
            recent_qs = User.objects.filter(last_login__gte=recent_threshold).exclude(id=request.user.id).select_related('perfil')
            if q:
                recent_qs = recent_qs.filter(username__icontains=q)

        ordered_recent = list(recent_qs.order_by('-last_login')[:limit])
        if not ordered_recent:
            online_total_count = 1 if self_online else 0
            return JsonResponse({'count': 0, 'online_count': 0, 'online_total_count': online_total_count, 'self_online': self_online, 'players': []})

        friend_ids = set(request.user.perfil.amigos.values_list('id', flat=True))
        payload_recent = []
        for user_obj in ordered_recent:
            privacy = getattr(user_obj, 'privacy_settings', None)
            if privacy and not privacy.show_online_status:
                continue

            last_seen_dt = get_user_last_seen(user_obj.id) or user_obj.last_login
            payload_recent.append({
                'id': user_obj.id,
                'username': user_obj.username,
                'avatar_url': user_obj.perfil.foto.url if user_obj.perfil.foto else '',
                'esporte': getattr(user_obj.perfil, 'esportes_preferidos', '') or 'Nao informado',
                'nivel': getattr(user_obj.perfil, 'nivel_habilidade', '') or 'Nao informado',
                'is_friend': user_obj.id in friend_ids,
                'is_online': False,
                'last_seen_label': _format_last_seen_label(last_seen_dt),
            })

        online_total_count = (1 if self_online else 0)
        return JsonResponse({'count': len(payload_recent), 'online_count': 0, 'online_total_count': online_total_count, 'self_online': self_online, 'players': payload_recent})

    friend_ids = set(request.user.perfil.amigos.values_list('id', flat=True))

    ordered_users = []
    for user_id in online_ids:
        user_obj = online_by_id.get(user_id)
        if user_obj:
            ordered_users.append(user_obj)

    ordered_users.sort(key=lambda u: (u.id not in friend_ids, u.username.lower()))

    payload_players = []
    for user_obj in ordered_users[:limit]:
        privacy = getattr(user_obj, 'privacy_settings', None)
        if privacy and not privacy.show_online_status:
            continue

        last_seen_dt = get_user_last_seen(user_obj.id) or user_obj.last_login
        payload_players.append({
            'id': user_obj.id,
            'username': user_obj.username,
            'avatar_url': user_obj.perfil.foto.url if user_obj.perfil.foto else '',
            'esporte': getattr(user_obj.perfil, 'esportes_preferidos', '') or 'Nao informado',
            'nivel': getattr(user_obj.perfil, 'nivel_habilidade', '') or 'Nao informado',
            'is_friend': user_obj.id in friend_ids,
            'is_online': user_obj.id in online_id_set,
            'last_seen_label': _format_last_seen_label(last_seen_dt),
        })

    online_count = sum(1 for item in payload_players if item['is_online'])
    online_total_count = online_count + (1 if self_online else 0)
    return JsonResponse({'count': len(payload_players), 'online_count': online_count, 'online_total_count': online_total_count, 'self_online': self_online, 'players': payload_players})