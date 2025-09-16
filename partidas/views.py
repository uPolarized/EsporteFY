from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Partida
from .forms import PartidaForm
from django.views.generic import ListView # Adicione ListView
from django.utils import timezone # Importa a funcionalidade de tempo
from django.forms import modelformset_factory
from .forms import AvaliacaoQuadraForm, AvaliacaoJogadorForm
from .models import AvaliacaoQuadra, AvaliacaoJogador
from quadras.models import Quadra # Importe o modelo Quadra


class CriarPartidaView(LoginRequiredMixin, CreateView):
    model = Partida
    form_class = PartidaForm
    template_name = 'partidas/criar_partida.html'
    success_url = reverse_lazy('feed')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Envia a lista de todas as quadras para o template
        context['quadras'] = Quadra.objects.all()
        return context

    def form_valid(self, form):
        form.instance.organizador = self.request.user
        messages.success(self.request, "Sua partida foi criada e já está visível para outros jogadores!")
        response = super().form_valid(form)
        self.object.jogadores_confirmados.add(self.request.user)
        return response

# --- NOVAS VIEWS PARA PARTICIPAR E SAIR ---
@login_required
def participar_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    
    if request.user in partida.jogadores_confirmados.all():
        messages.warning(request, 'Você já está participando desta partida.')
    elif partida.vagas_restantes > 0:
        partida.jogadores_confirmados.add(request.user)
        messages.success(request, 'Você entrou na partida! Nos vemos lá.')
    else:
        messages.error(request, 'Esta partida já está lotada.')
        
    return redirect('feed')

@login_required
def sair_da_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    
    if request.user == partida.organizador:
        messages.error(request, 'Você é o organizador e não pode sair da partida. Considere cancelá-la.')
    elif request.user in partida.jogadores_confirmados.all():
        partida.jogadores_confirmados.remove(request.user)
        messages.info(request, 'Você saiu da partida.')
    else:
        messages.warning(request, 'Você não estava participando desta partida.')

    return redirect('feed')


class MinhasPartidasView(LoginRequiredMixin, ListView):
    model = Partida
    template_name = 'partidas/minhas_partidas.html'
    context_object_name = 'partidas'

    def get_queryset(self):
        # Filtra as partidas para incluir apenas aquelas em que o usuário está confirmado
        # e ordena pelas mais recentes primeiro.
        return self.request.user.partidas_confirmadas.all().order_by('-data_hora')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # Separa a lista de partidas em duas: futuras e passadas
        context['partidas_futuras'] = self.get_queryset().filter(data_hora__gte=now)
        context['partidas_passadas'] = self.get_queryset().filter(data_hora__lt=now)
        # Remove a lista original para evitar confusão
        del context['partidas']
        return context
    






@login_required
def avaliar_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    avaliador = request.user

    # Impede que o usuário avalie uma partida que já avaliou
    if AvaliacaoQuadra.objects.filter(partida=partida, avaliador=avaliador).exists():
        messages.warning(request, "Você já avaliou esta partida.")
        return redirect('partidas:minhas_partidas')

    # Pega a lista de outros jogadores para avaliar
    outros_jogadores = partida.jogadores_confirmados.exclude(id=avaliador.id)
    
    # Cria um "FormSet", um conjunto de formulários para avaliar cada jogador
    AvaliacaoJogadorFormSet = modelformset_factory(AvaliacaoJogador, form=AvaliacaoJogadorForm, extra=len(outros_jogadores))

    if request.method == 'POST':
        quadra_form = AvaliacaoQuadraForm(request.POST)
        jogador_formset = AvaliacaoJogadorFormSet(request.POST)

        if quadra_form.is_valid() and jogador_formset.is_valid():
            # Salva a avaliação da quadra
            avaliacao_quadra = quadra_form.save(commit=False)
            avaliacao_quadra.partida = partida
            avaliacao_quadra.avaliador = avaliador
            avaliacao_quadra.save()

            # Salva a avaliação de cada jogador
            for i, form in enumerate(jogador_formset):
                if form.cleaned_data:
                    avaliacao_jogador = form.save(commit=False)
                    avaliacao_jogador.partida = partida
                    avaliacao_jogador.avaliador = avaliador
                    avaliacao_jogador.avaliado = outros_jogadores[i]
                    avaliacao_jogador.save()
            
            messages.success(request, "Obrigado pela sua avaliação!")
            return redirect('partidas:minhas_partidas')
    else:
        quadra_form = AvaliacaoQuadraForm()
        jogador_formset = AvaliacaoJogadorFormSet(queryset=AvaliacaoJogador.objects.none())

    # Agrupa cada formulário com o jogador correspondente para exibir no template
    forms_e_jogadores = zip(jogador_formset.forms, outros_jogadores)

    context = {
        'partida': partida,
        'quadra_form': quadra_form,
        'jogador_formset': jogador_formset, # Necessário para o management_form
        'forms_e_jogadores': forms_e_jogadores,
    }
    return render(request, 'partidas/avaliar_partida.html', context)