import json
import redis
import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder

from .models import Mensagem, Atividade

# Configura logger para debug
logger = logging.getLogger(__name__)

# Conecta ao Redis usando a configuração do settings
REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
try:
    r = redis.from_url(REDIS_URL)
except Exception as e:
    logger.error(f"Erro ao conectar no Redis pelos Signals: {e}")
    r = None

# ---------------------------------------------------------
# 1. NOTIFICAÇÃO NO SININHO (Topo do site)
# ---------------------------------------------------------
@receiver(post_save, sender=Mensagem)
def enviar_notificacao_nova_mensagem(sender, instance, created, **kwargs):
    if created and r:
        try:
            conversa = instance.conversa
            remetente = instance.remetente
            
            # Pega a foto com segurança
            foto_url = ""
            if hasattr(remetente, 'perfil') and remetente.perfil.foto:
                try:
                    foto_url = remetente.perfil.foto.url
                except ValueError:
                    pass

            # Monta o payload da notificação
            data = {
                'type': 'notification',  # Tipo para o Frontend saber o que fazer
                'remetente': remetente.username,
                'mensagem': instance.conteudo[:40] if instance.conteudo else "Nova imagem",
                'foto_url': foto_url,
                'conversa_url': reverse('social:conversa', kwargs={'username': remetente.username}),
                'timestamp': instance.timestamp.strftime("%H:%M")
            }

            # Envia para os destinatários
            for participante in conversa.participantes.exclude(id=remetente.id):
                channel_name = f"notifications_user_{participante.id}"
                r.publish(channel_name, json.dumps(data))
                logger.info(f"🔔 Notificação enviada para {channel_name}")

        except Exception as e:
            logger.error(f"Erro no signal de mensagem: {e}")

# ---------------------------------------------------------
# 2. ATUALIZAÇÃO DO FEED (Centro da tela)
# ---------------------------------------------------------
@receiver(post_save, sender=Atividade)
def broadcast_atividade(sender, instance, created, **kwargs):
    if created and r:
        try:
            # Prepara o alvo
            alvo_str = str(instance.alvo) if instance.alvo else ""
            
            # Prepara a inicial
            ator_initial = instance.ator.username[0].upper() if instance.ator else "?"
            
            data = {
                "type": "feed_update", # Tipo para o Frontend diferenciar
                "id": instance.id,
                "ator": instance.ator.username if instance.ator else "Usuário",
                "ator_initial": ator_initial,
                "verbo": instance.verbo,
                "alvo": alvo_str,
                "timestamp": instance.timestamp.strftime("%H:%M"),
            }

            # Publica no canal que o FastAPI está escutando
            # Obs: O FastAPI escuta 'notifications_*', então vamos usar esse prefixo
            # para garantir que ele pegue, ou você pode adicionar 'feed' no app.py
            channel_name = "notifications_feed" 
            
            r.publish(channel_name, json.dumps(data, cls=DjangoJSONEncoder))
            logger.info(f"📰 Atividade publicada no feed: {channel_name}")

        except Exception as e:
            logger.error(f"Erro no signal de atividade: {e}")