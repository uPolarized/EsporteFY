from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Conversa, Mensagem
from .forms import MensagemForm

class CaixaDeEntradaView(LoginRequiredMixin, View):
    """
    Exibe a lista de todas as conversas do utilizador logado.
    """
    def get(self, request):
        conversas = Conversa.objects.filter(participantes=request.user)
        return render(request, 'social/caixa_de_entrada.html', {'conversas': conversas})

class ConversaView(LoginRequiredMixin, View):
    """
    Exibe uma conversa específica entre dois utilizadores e processa o envio de novas mensagens.
    """
    def get(self, request, username):
        # Encontra o outro utilizador com quem se está a conversar
        outro_usuario = get_object_or_404(User, username=username)
        
        # Encontra a conversa existente entre o utilizador logado e o outro utilizador
        conversa = Conversa.objects.filter(
            participantes=request.user
        ).filter(
            participantes=outro_usuario
        ).first()
        
        # Pega as mensagens da conversa, se ela existir
        mensagens = conversa.mensagens.all() if conversa else []
        form = MensagemForm()
        
        context = {
            'outro_usuario': outro_usuario,
            'mensagens': mensagens,
            'form': form,
        }
        return render(request, 'social/conversa.html', context)

    def post(self, request, username):
        # Esta função é executada quando o utilizador envia uma mensagem
        outro_usuario = get_object_or_404(User, username=username)
        
        # Encontra a conversa entre os dois utilizadores. Se não existir, cria uma.
        conversa, criada = Conversa.objects.filter(
            participantes=request.user
        ).filter(
            participantes=outro_usuario
        ).get_or_create()

        form = MensagemForm(request.POST)
        if form.is_valid():
            # Cria o objeto da mensagem e guarda-o na base de dados
            mensagem = Mensagem(
                conversa=conversa,
                remetente=request.user,
                conteudo=form.cleaned_data['conteudo']
            )
            mensagem.save()
        
        # Redireciona de volta para a mesma página, que agora mostrará a nova mensagem
        return redirect('social:conversa', username=username)
