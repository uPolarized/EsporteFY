import redis
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

def get_redis_client():
    """
    Retorna uma instância do cliente Redis configurada com a URL do settings.
    """
    try:
        # Cria a conexão usando a URL definida no settings.py (redis://redis:6379/0)
        return redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis: {e}")
        return None

def publish_to_redis(channel_name, data):
    """
    Publica uma mensagem JSON em um canal específico do Redis.
    Isso substitui o 'group_send' do Django Channels.
    """
    client = get_redis_client()
    if client:
        try:
            # Converte o dicionário Python para string JSON
            message_json = json.dumps(data)
            # Publica no canal (ex: 'notifications_user_4')
            client.publish(channel_name, message_json)
        except Exception as e:
            logger.error(f"Erro ao publicar no Redis: {e}")
    else:
        logger.warning("Redis não disponível. Mensagem não enviada.")