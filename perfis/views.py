from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Perfil, SolicitacaoAmizade
from .forms import PerfilForm, FiltroUsuarioForm

# Importamos o modelo Partida para poder contar as partidas
from partidas.models import Partida 
# (Se o seu app de partidas tiver um nome diferente, apenas corrija a importação)

class ListaUsuariosView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'perfis/lista_usuarios.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).select_related('perfil')
        form = FiltroUsuarioForm(self.request.GET)
        if form.is_valid():
            nome = form.cleaned_data.get('nome_usuario')
            esporte = form.cleaned_data.get('esporte')
            nivel = form.cleaned_data.get('nivel')
            if nome:
                queryset = queryset.filter(username__icontains=nome)
            if esporte:
                queryset = queryset.filter(perfil__esportes_preferidos=esporte)
            if nivel:
                queryset = queryset.filter(perfil__nivel_habilidade=nivel)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['filtro_form'] = FiltroUsuarioForm(self.request.GET or None)
        amigos = user.perfil.amigos.all()
        solicitacoes_enviadas_qs = SolicitacaoAmizade.objects.filter(solicitante=user)
        solicitacoes_recebidas_qs = SolicitacaoAmizade.objects.filter(receptor=user)
        context['amigos_lista'] = list(amigos)
        context['enviadas_lista'] = [s.receptor for s in solicitacoes_enviadas_qs]
        context['recebidas_lista'] = [s.solicitante for s in solicitacoes_recebidas_qs]
        return context

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
    return redirect('perfis:meu_perfil') # <-- CORRIGIDO AQUI

@login_required
def recusar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoAmizade, id=solicitacao_id)
    if solicitacao.receptor == request.user:
        solicitacao.delete()
        messages.info(request, f"Pedido de amizade de {solicitacao.solicitante.username} recusado.")
    else:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
    return redirect('perfis:meu_perfil') # <-- CORRIGIDO AQUI

class MeuPerfilView(LoginRequiredMixin, DetailView):
    model = Perfil
    template_name = 'perfis/meu_perfil.html' 
    context_object_name = 'object' # Adicionado para corresponder ao template
    
    def get_object(self):
        return self.request.user.perfil
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object já é o Perfil, pego pelo get_object()
        perfil_logado = self.object 

        context['solicitacoes_pendentes'] = SolicitacaoAmizade.objects.filter(receptor=self.request.user, aceito=False)
        
        # --- ATUALIZADO ---
        # Contagem de amigos (presumindo M2M 'amigos' no modelo Perfil)
        context['total_amigos'] = perfil_logado.amigos.count()
        
        # CORREÇÃO: Usando 'jogadores_confirmados' como o erro indicou
        context['total_partidas'] = Partida.objects.filter(jogadores_confirmados=perfil_logado.user).count()
        # --- FIM DA ATUALIZAÇÃO ---

        return context

class VerPerfilView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'perfis/ver_perfil.html' # Este template precisa ser ajustado
    context_object_name = 'object' # Mudado de 'perfil_usuario' para 'object'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_logado = self.request.user
        
        # self.object agora é o User (devido ao model = User)
        perfil_visitado_user = self.get_object() 
        perfil_visitado_perfil = perfil_visitado_user.perfil 
        
        context['ja_sao_amigos'] = user_logado.perfil.amigos.filter(id=perfil_visitado_user.id).exists()
        context['pedido_enviado'] = SolicitacaoAmizade.objects.filter(solicitante=user_logado, receptor=perfil_visitado_user).exists()
        context['pedido_recebido'] = SolicitacaoAmizade.objects.filter(solicitante=perfil_visitado_user, receptor=user_logado).exists()

        # --- ATUALIZADO ---
        # Contagens para o perfil que está sendo visitado
        context['total_amigos'] = perfil_visitado_perfil.amigos.count()
        
        # CORREÇÃO: Usando 'jogadores_confirmados' aqui também
        context['total_partidas'] = Partida.objects.filter(jogadores_confirmados=perfil_visitado_user).count()
        # --- FIM DA ATUALIZAÇÃO ---

        return context

class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'perfis/editar_perfil.html'
    success_url = reverse_lazy('perfis:meu_perfil') # <-- CORRIGIDO AQUI
    def get_object(self):
        return self.request.user.perfil

@login_required
def remover_amigo(request, user_id):
    amigo_a_remover = get_object_or_404(User, id=user_id)
    usuario_logado = request.user
    usuario_logado.perfil.amigos.remove(amigo_a_remover)
    amigo_a_remover.perfil.amigos.remove(usuario_logado)
    messages.info(request, f"Você não é mais amigo(a) de {amigo_a_remover.username}.")
    return redirect('perfis:ver_perfil', username=amigo_a_remover.username)