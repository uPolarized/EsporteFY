from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.forms import modelformset_factory
from django.contrib.contenttypes.models import ContentType
from .models import Partida, AvaliacaoQuadra, AvaliacaoJogador
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
        messages.success(self.request, "A sua partida foi criada e já está visível para outros jogadores!")
        
        # 1. O super().form_valid salva a partida no banco.
        # 2. O salvamento dispara o 'post_save' no signals.py.
        # 3. O signal cria a Atividade automaticamente.
        response = super().form_valid(form) 
        
        # Adiciona o organizador aos jogadores confirmados
        self.object.jogadores_confirmados.add(self.request.user)

        # --- REMOVIDO ---
        # A criação manual da atividade foi removida daqui para evitar duplicidade.
        # O signal já está fazendo esse trabalho.
        
        return response

# ... (Mantenha o resto do arquivo igual, apenas a classe CriarPartidaView precisava de alteração) ...

# ---------------------------------------------------------
# ✅ PARTICIPAR DE UMA PARTIDA (com limpeza de atividades antigas)
# ---------------------------------------------------------
@login_required
@require_POST
@transaction.atomic
def participar_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_related('organizador').prefetch_related('jogadores_confirmados'),
        id=partida_id
    )
    user = request.user

    if user in partida.jogadores_confirmados.all():
        messages.warning(request, "Você já está participando desta partida.")
        return redirect('feed')

    if partida.vagas_restantes <= 0:
        messages.error(request, "Esta partida está lotada.")
        return redirect('feed')

    # Adiciona o jogador
    partida.jogadores_confirmados.add(user)

    content_type = ContentType.objects.get_for_model(Partida)

    # 🧹 Remove qualquer "saiu da partida" anterior para limpar o feed
    Atividade.objects.filter(
        ator=user,
        verbo__icontains="saiu",
        content_type=content_type,
        object_id=partida.id
    ).delete()

    messages.success(request, f"Você entrou na partida '{partida.titulo}'.")
    return redirect('feed')

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
            'Você é o organizador e não pode sair da partida. Considere cancelá-la.'
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
        messages.warning(request, 'Você não estava participando desta partida.')

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

    messages.success(request, "Partida cancelada com sucesso!")
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