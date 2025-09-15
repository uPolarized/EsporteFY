from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Perfil, SolicitacaoAmizade
from .forms import PerfilForm

# --- A VIEW QUE ESTAVA FALTANDO ---
class ListaUsuariosView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'perfis/lista_usuarios.html'
    context_object_name = 'usuarios'

    def get_queryset(self):
        # Exclui o próprio usuário da lista para não adicionar a si mesmo
        return User.objects.exclude(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Busca os status de amizade para exibir os botões corretos no template
        amigos = user.perfil.amigos.all()
        solicitacoes_enviadas_qs = SolicitacaoAmizade.objects.filter(solicitante=user)
        solicitacoes_recebidas_qs = SolicitacaoAmizade.objects.filter(receptor=user)

        context['amigos_lista'] = list(amigos)
        context['enviadas_lista'] = [s.receptor for s in solicitacoes_enviadas_qs]
        context['recebidas_lista'] = [s.solicitante for s in solicitacoes_recebidas_qs]
        
        return context

# --- VIEW PARA ENVIAR SOLICITAÇÃO (Também estava faltando) ---
@login_required
def enviar_solicitacao_amizade(request, receptor_id):
    receptor = get_object_or_404(User, id=receptor_id)
    solicitante = request.user

    if not SolicitacaoAmizade.objects.filter(solicitante=solicitante, receptor=receptor).exists() and not SolicitacaoAmizade.objects.filter(solicitante=receptor, receptor=solicitante).exists():
        SolicitacaoAmizade.objects.create(solicitante=solicitante, receptor=receptor)
        messages.success(request, f'Pedido de amizade enviado para {receptor.username}.')
    else:
        messages.warning(request, f'Já existe uma solicitação ou amizade com {receptor.username}.')

    return redirect('perfis:lista_usuarios')

# --- SUAS VIEWS EXISTENTES (Corretas) ---
class PerfilView(LoginRequiredMixin, DetailView):
    model = Perfil
    template_name = 'perfis/perfil.html'

    def get_object(self):
        return self.request.user.perfil

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solicitacoes_pendentes'] = SolicitacaoAmizade.objects.filter(receptor=self.request.user, aceito=False)
        return context

class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'perfis/editar_perfil.html'
    success_url = reverse_lazy('perfis:perfil')

    def get_object(self):
        return self.request.user.perfil

@login_required
def aceitar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoAmizade, id=solicitacao_id)
    
    if solicitacao.receptor == request.user:
        solicitacao.receptor.perfil.amigos.add(solicitacao.solicitante)
        solicitacao.solicitante.perfil.amigos.add(solicitacao.receptor)
        solicitacao.delete()
        messages.success(request, f"Você e {solicitacao.solicitante.username} agora são amigos!")
    else:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        
    return redirect('perfis:perfil')

@login_required
def recusar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoAmizade, id=solicitacao_id)
    
    if solicitacao.receptor == request.user:
        solicitacao.delete()
        messages.info(request, f"Pedido de amizade de {solicitacao.solicitante.username} recusado.")
    else:
        messages.error(request, "Você não tem permissão para realizar esta ação.")

    return redirect('perfis:perfil')