import os
import json
import redis
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Conversa, Mensagem
from .forms import MensagemForm
from .utils.image_moderation import analisar_imagem


# ==========================
# 💬 VIEW: PÁGINA DE CONVERSA
# ==========================
class ConversaView(LoginRequiredMixin, View):
    def get(self, request, username):
        outro_usuario = get_object_or_404(User, username=username)

        conversa = (
            Conversa.objects.filter(participantes=request.user)
            .filter(participantes=outro_usuario)
            .first()
        )
        mensagens = conversa.mensagens.all() if conversa else []
        form = MensagemForm()

        conversas_usuario = []
        for c in Conversa.objects.filter(participantes=request.user).distinct():
            outro = c.participantes.exclude(id=request.user.id).first()
            if outro:
                conversas_usuario.append(
                    {
                        "outro": outro,
                        "ultima_mensagem": c.mensagens.last(),
                    }
                )

        context = {
            "outro_usuario": outro_usuario,
            "mensagens": mensagens,
            "form": form,
            "conversas_usuario": conversas_usuario,
        }
        return render(request, "social/conversa.html", context)


# ====================================
# 💬 VIEW: ENVIO DE MENSAGENS + REDIS
# ====================================
@login_required
def enviar_mensagem(request, username):
    """Recebe a mensagem via POST, salva no banco e publica no Redis (para o FastAPI)."""
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    conteudo = request.POST.get("conteudo", "").strip()
    imagem = request.FILES.get("imagem")

    if not conteudo and not imagem:
        return JsonResponse({"error": "Mensagem vazia"}, status=400)

    outro_usuario = get_object_or_404(User, username=username)

    # === 💬 BUSCA OU CRIA CONVERSA ENTRE OS DOIS USUÁRIOS ===
    conversa_qs = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario)
    if conversa_qs.exists():
        conversa = conversa_qs.first()
    else:
        conversa = Conversa.objects.create()
        conversa.participantes.add(request.user, outro_usuario)

    # === 🚨 MODERAÇÃO DE IMAGEM (Google Vision) ===
    if imagem:
        os.makedirs("media/temp", exist_ok=True)
        caminho_temporario = os.path.join("media/temp", imagem.name)

        with open(caminho_temporario, "wb+") as destino:
            for chunk in imagem.chunks():
                destino.write(chunk)

        try:
            is_safe, details = analisar_imagem(caminho_temporario)
            print("🧠 Resultado da moderação:", details)
        except Exception as e:
            print("⚠️ Erro inesperado ao analisar imagem:", e)
            is_safe = True
            details = {"error": str(e)}

        try:
            os.remove(caminho_temporario)
        except Exception:
            pass

        if not is_safe:
            return JsonResponse(
                {
                    "error": "🚫 Imagem bloqueada: conteúdo impróprio detectado.",
                    "blocked": True,
                    "details": details,
                },
                status=400,
            )

    # === 💬 CRIA A MENSAGEM ===
    mensagem = Mensagem.objects.create(
        conversa=conversa,
        remetente=request.user,
        conteudo=conteudo,
        imagem=imagem if imagem else None,
    )

    # === ⏰ MONTA OS DADOS PARA ENVIAR VIA WEBSOCKET ===
    timestamp_local = mensagem.timestamp.astimezone(
        timezone.get_current_timezone()
    ).strftime("%H:%M")

    data_msg = {
        "type": "chat_message",
        "message": mensagem.conteudo or "",
        "username": mensagem.remetente.username,
        "user_avatar_url": (
            mensagem.remetente.perfil.foto.url
            if hasattr(mensagem.remetente, "perfil")
            and mensagem.remetente.perfil.foto
            else ""
        ),
        "timestamp": timestamp_local,
        "image_url": mensagem.imagem.url if mensagem.imagem else None,
    }

    # === 📡 PUBLICA NO REDIS (FastAPI vai captar e retransmitir) ===
    try:
        redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
        group_name = f"chat_{'_'.join(sorted([request.user.username, outro_usuario.username]))}"
        redis_client.publish(group_name, json.dumps(data_msg))
        print(f"📡 Enviado ao Redis canal: {group_name}")
    except Exception as e:
        print(f"❌ Erro ao publicar no Redis: {e}")

    return JsonResponse({"success": True, "message": "Mensagem enviada com sucesso."})
