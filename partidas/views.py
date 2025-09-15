from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Partida
from .forms import PartidaForm

class CriarPartidaView(LoginRequiredMixin, CreateView):
    model = Partida
    form_class = PartidaForm
    template_name = 'partidas/criar_partida.html'
    success_url = reverse_lazy('feed')

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