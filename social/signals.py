from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from partidas.models import Partida 
from django.urls import reverse
from asgiref.sync import async_to_sync
from social.models import Atividade
from channels.layers import get_channel_layer
from .models import Mensagem
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
import json



@receiver(post_save, sender=Mensagem)
def enviar_notificacao_nova_mensagem(sender, instance, created, **kwargs):
    if created:
        conversa = instance.conversa
        remetente = instance.remetente
        
        # Encontra todos os destinatários da mensagem (excluindo quem enviou)
        for participante in conversa.participantes.exclude(id=remetente.id):
            channel_layer = get_channel_layer()
            
            # Envia a notificação para o grupo específico do destinatário
            async_to_sync(channel_layer.group_send)(
                f'notifications_user_{participante.id}',
                {
                    'type': 'send_notification',
                    'remetente': remetente.username,
                    'conversa_url': reverse('social:conversa', kwargs={'username': remetente.username})
                }
            )

@receiver(post_save, sender=Atividade)
def broadcast_atividade(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    data = {
        "id": instance.id,
        "ator": instance.ator.username if instance.ator else "Usuário",
        "verbo": instance.verbo,
        "timestamp": instance.timestamp.strftime("%H:%M"),
    }

    async_to_sync(channel_layer.group_send)(
        "feed",
        {"type": "nova_atividade", "data": json.dumps(data, cls=DjangoJSONEncoder)},
    )