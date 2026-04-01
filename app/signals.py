from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import DataAccessRequest
from app.redis_utils import publish_to_redis


@receiver(post_save, sender=DataAccessRequest)
def notify_data_access_ready(sender, instance, created, **kwargs):
    if created:
        return

    if (
        instance.status == DataAccessRequest.STATUS_COMPLETED
        and instance.arquivo_exportacao
        and instance.user_id
    ):
        publish_to_redis(
            f"notifications_user_{instance.user_id}",
            {
                "type": "notification",
                "remetente": "EsporteFY",
                "mensagem": "Seu arquivo de dados pessoais está pronto para download.",
                "conversa_url": "/lgpd/?tab=meus-dados",
                "timestamp": "agora",
            },
        )
