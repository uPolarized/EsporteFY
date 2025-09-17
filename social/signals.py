from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from partidas.models import Partida 
from django.urls import reverse
from asgiref.sync import async_to_sync
from social.models import Atividade
from channels.layers import get_channel_layer
from .models import Mensagem

@receiver(post_save, sender=Partida)
def criar_atividade_nova_partida(sender, instance, created, **kwargs):
    if created:
        Atividade.objects.create(ator=instance.organizador, verbo='criou a partida', alvo=instance)

@receiver(m2m_changed, sender=Partida.jogadores_confirmados.through)
def criar_atividade_novo_jogador(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_pk in pk_set:
            jogador = User.objects.get(pk=user_pk)
            if jogador != instance.organizador:
                Atividade.objects.create(ator=jogador, verbo='entrou na partida', alvo=instance)

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