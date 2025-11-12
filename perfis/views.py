from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from allauth.account.views import PasswordSetView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Perfil, SolicitacaoAmizade
from .forms import PerfilForm, FiltroUsuarioForm
from partidas.models import Partida
from .forms import SetPasswordCaptchaForm

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


# ============================================================
# SOLICITAÇÕES DE AMIZADE
# ============================================================
@login_required
def enviar_solicitacao_amizade(request, receptor_id):
    receptor = get_object_or_404(User, id=receptor_id)
    solicitante = request.user

    ja_existe = (
        SolicitacaoAmizade.objects.filter(solicitante=solicitante, receptor=receptor).exists() or
        SolicitacaoAmizade.objects.filter(solicitante=receptor, receptor=solicitante).exists()
    )

    if not ja_existe:
        solicitacao = SolicitacaoAmizade.objects.create(
            solicitante=solicitante,
            receptor=receptor
        )

        # 🚀 Envia notificação via WebSocket com username e IDs
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_user_{receptor.id}',
            {
                'type': 'send_generic_notification',
                'titulo': 'Novo pedido de amizade 🤝',
                'mensagem': f'{solicitante.username} te enviou um pedido de amizade!',
                'solicitacao_id': solicitacao.id,
                'solicitante_id': solicitante.id,
                'solicitante_username': solicitante.username,
            }
        )

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
        solicitante = solicitacao.solicitante
        solicitacao.delete()

        messages.success(request, f"Você e {solicitante.username} agora são amigos!")

        # 🚀 Envia notificação de amizade aceita (para o solicitante original)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_user_{solicitante.id}',
            {
                'type': 'send_generic_notification',
                'titulo': 'Amizade aceita 🎉',
                'mensagem': f'{request.user.username} aceitou seu pedido de amizade!',
                'solicitante_id': solicitante.id,
                'solicitante_username': solicitante.username,
            }
        )

    else:
        messages.error(request, "Você não tem permissão para realizar esta ação.")

    return redirect('perfis:meu_perfil')


@login_required
def recusar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoAmizade, id=solicitacao_id)
    if solicitacao.receptor == request.user:
        solicitante = solicitacao.solicitante
        receptor = solicitacao.receptor

        solicitacao.delete()
        messages.info(request, f"Pedido de amizade de {solicitante.username} recusado.")

        # 🚀 Notifica o solicitante em tempo real
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_user_{solicitante.id}',
            {
                'type': 'send_generic_notification',
                'titulo': 'Pedido de amizade recusado',
                'mensagem': f'{receptor.username} recusou seu pedido 😢',
                'acao': 'amizade_recusada',
                'usuario_id': receptor.id,
                'solicitante_id': solicitante.id,
                'solicitante_username': solicitante.username,
            }
        )
    else:
        messages.error(request, "Você não tem permissão para realizar esta ação.")

    return redirect('perfis:meu_perfil')


@login_required
def remover_amigo(request, user_id):
    amigo_a_remover = get_object_or_404(User, id=user_id)
    usuario_logado = request.user

    usuario_logado.perfil.amigos.remove(amigo_a_remover)
    amigo_a_remover.perfil.amigos.remove(usuario_logado)

    messages.info(request, f"Você não é mais amigo(a) de {amigo_a_remover.username}.")
    return redirect('perfis:ver_perfil', username=amigo_a_remover.username)


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

        context['solicitacoes_pendentes'] = SolicitacaoAmizade.objects.filter(
            receptor=self.request.user,
            aceito=False
        )
        context['total_amigos'] = perfil_logado.amigos.count()
        context['total_partidas'] = Partida.objects.filter(
            jogadores_confirmados=perfil_logado.user
        ).count()

        return context


# ============================================================
# VISUALIZAR PERFIL DE OUTROS USUÁRIOS
# ============================================================
class VerPerfilView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'perfis/ver_perfil.html'
    context_object_name = 'object'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_logado = self.request.user
        perfil_visitado_user = self.get_object()
        perfil_visitado_perfil = perfil_visitado_user.perfil

        context['ja_sao_amigos'] = user_logado.perfil.amigos.filter(
            id=perfil_visitado_user.id
        ).exists()

        context['pedido_enviado'] = SolicitacaoAmizade.objects.filter(
            solicitante=user_logado,
            receptor=perfil_visitado_user
        ).exists()

        context['pedido_recebido'] = SolicitacaoAmizade.objects.filter(
            solicitante=perfil_visitado_user,
            receptor=user_logado
        ).exists()

        context['total_amigos'] = perfil_visitado_perfil.amigos.count()
        context['total_partidas'] = Partida.objects.filter(
            jogadores_confirmados=perfil_visitado_user
        ).count()

        return context


# ============================================================
# EDITAR PERFIL
# ============================================================
class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'perfis/editar_perfil.html'
    success_url = reverse_lazy('perfis:meu_perfil')

    def get_object(self):
        return self.request.user.perfil


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
