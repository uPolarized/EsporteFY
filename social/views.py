import os
import json
import redis
import logging
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Conversa, Mensagem, LikeAtividade, Atividade
from .forms import MensagemForm
from .utils.image_moderation import analisar_imagem

# Configuração de Log para ver o erro no terminal
logger = logging.getLogger(__name__)

# Garante a URL do Redis correta para o Docker
REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')

class ConversaView(LoginRequiredMixin, View):
    def get(self, request, username):
        outro_usuario = get_object_or_404(User, username=username)
        
        # Busca ou cria conversa
        conversa = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario).first()
        
        mensagens = []
        if conversa:
            mensagens = conversa.mensagens.all().order_by('timestamp')

        form = MensagemForm()

        # Sidebar ordenada pela data da última mensagem
        try:
            conversas_qs = Conversa.objects.filter(participantes=request.user).order_by('-ultima_mensagem_data')
        except Exception:
            # Fallback se a migração não tiver sido feita corretamente
            conversas_qs = Conversa.objects.filter(participantes=request.user)

        conversas_usuario = []
        for c in conversas_qs:
            outro = c.participantes.exclude(id=request.user.id).first()
            if outro:
                conversas_usuario.append({
                    "outro": outro,
                    "ultima_mensagem": c.mensagens.last(),
                })

        context = {
            "outro_usuario": outro_usuario,
            "mensagens": mensagens,
            "form": form,
            "conversas_usuario": conversas_usuario,
        }
        return render(request, "social/conversa.html", context)

@login_required
def enviar_mensagem(request, username):
    """
    API que recebe a mensagem, salva no Postgres e avisa o Redis.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    conteudo = request.POST.get("conteudo", "").strip()
    imagem = request.FILES.get("imagem")

    if not conteudo and not imagem:
        return JsonResponse({"error": "Mensagem vazia"}, status=400)

    outro_usuario = get_object_or_404(User, username=username)

    # 1. BANCO DE DADOS (Postgres)
    try:
        conversa = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario).first()
        if not conversa:
            conversa = Conversa.objects.create()
            conversa.participantes.add(request.user, outro_usuario)

        # Salva a mensagem
        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            conteudo=conteudo,
            imagem=imagem if imagem else None,
        )
        
        # Atualiza data da conversa
        conversa.ultima_mensagem_data = timezone.now()
        conversa.save()
        
        print(f"✅ [Django] Mensagem {mensagem.id} salva no Banco.")

    except Exception as e:
        print(f"❌ [Django] Erro ao salvar no Banco: {e}")
        return JsonResponse({"error": f"Erro de Banco de Dados: {str(e)}"}, status=500)

    # 2. REAL-TIME (Redis) - DIAGNÓSTICO
    try:
        timestamp_local = mensagem.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M")
        
        user_avatar = ""
        if hasattr(mensagem.remetente, "perfil") and mensagem.remetente.perfil.foto:
            user_avatar = mensagem.remetente.perfil.foto.url

        data_msg = {
            "type": "chat_message",
            "message": mensagem.conteudo or "",
            "username": mensagem.remetente.username,
            "user_avatar_url": user_avatar,
            "timestamp": timestamp_local,
            "image_url": mensagem.imagem.url if mensagem.imagem else None,
        }

        # Conexão
        # OBS: Se estiver imprimindo 'redis://redis:6379/0', está certo para Docker.
        print(f"🔌 [Django] Conectando Redis em: {REDIS_URL}")
        r = redis.from_url(REDIS_URL)
        
        # Nomes
        u1 = request.user.username.lower().strip()
        u2 = outro_usuario.username.lower().strip()
        
        room_members = sorted([u1, u2])
        group_name = f"chat_{'_'.join(room_members)}"
        
        # Publica e pega o NÚMERO DE RECEBEDORES
        recebedores = r.publish(group_name, json.dumps(data_msg))
        
        print(f"📡 [Django PUBLISH] Canal: '{group_name}' | Recebedores: {recebedores}")
        
        if recebedores == 0:
            print("⚠️ [ALERTA] Ninguém escutou! O FastAPI não está inscrito neste canal.")
            print("   -> Verifique se o FastAPI conectou no Redis.")
            print("   -> Verifique se o nome do canal no FastAPI é EXATAMENTE igual.")

    except Exception as e:
        print(f"❌ [Django ERRO REDIS] {e}")

    return JsonResponse({
        "success": True, 
        "message": "Enviada",
        "msg_id": mensagem.id
    })


@login_required
@require_POST
def toggle_like_atividade(request, atividade_id):
    """
    API para curtir/descurtir uma atividade.
    """
    atividade = get_object_or_404(Atividade, id=atividade_id)
    
    like, created = LikeAtividade.objects.get_or_create(
        atividade=atividade,
        usuario=request.user
    )
    
    if not created:
        # Se já existia, deleta (unlike)
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = atividade.likes.count()
    
    return JsonResponse({
        "success": True,
        "liked": liked,
        "like_count": like_count,
        "cta_label": "Curtido" if liked else "Curtir",
    })