from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Partida
from social.models import Atividade

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