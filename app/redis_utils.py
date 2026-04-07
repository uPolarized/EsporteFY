import redis
import logging
import json
from datetime import datetime, timezone
from django.contrib.auth.models import User
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

def is_user_online(user_identifier):
    """
    Verifica se um usuário está online consultando Redis.
    Args:
        user_identifier: user_id (int) ou username (str)
    Returns:
        bool: True se online, False caso contrário
    """
    client = get_redis_client()
    if client:
        try:
            result = client.exists(f"user_online:{user_identifier}")
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao verificar status online: {e}")
            return False
    return False


def get_user_last_seen(user_identifier):
    """
    Retorna o ultimo timestamp de presença salvo no Redis.
    Args:
        user_identifier: user_id (int) ou username (str)
    Returns:
        datetime|None: datetime UTC timezone-aware, ou None quando ausente/erro.
    """
    client = get_redis_client()
    if client:
        try:
            raw_value = client.get(f"user_last_seen:{user_identifier}")
            if not raw_value:
                return None

            timestamp = float(raw_value)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            logger.error(f"Erro ao obter ultimo visto: {e}")
            return None
    return None


def list_online_user_ids(max_items=200):
    """
    Lista ids de usuarios online com base nas chaves user_online:{id}.
    """
    client = get_redis_client()
    if not client:
        return []

    user_ids = []
    try:
        for key in client.scan_iter(match="user_online:*", count=200):
            if isinstance(key, bytes):
                key = key.decode('utf-8', errors='ignore')

            suffix = str(key).split(':')[-1]
            if suffix.isdigit():
                user_ids.append(int(suffix))
            else:
                try:
                    mapped_id = User.objects.filter(username=suffix).values_list('id', flat=True).first()
                    if mapped_id:
                        user_ids.append(int(mapped_id))
                except Exception:
                    pass

            if len(user_ids) >= max_items:
                break
    except Exception as e:
        logger.error(f"Erro ao listar usuarios online: {e}")
        return []

    # Remove duplicados preservando ordem.
    seen = set()
    deduped = []
    for uid in user_ids:
        if uid in seen:
            continue
        seen.add(uid)
        deduped.append(uid)

    return deduped