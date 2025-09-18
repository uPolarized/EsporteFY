from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from social.models import Atividade

@receiver(m2m_changed, sender=Perfil.amigos.through)
def criar_atividade_nova_amizade(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        quem_aceitou = instance.user
        for user_pk in pk_set:
            quem_enviou = User.objects.get(pk=user_pk)
            
            # CORREÇÃO: Cria apenas uma atividade, focada na ação de aceitar.
            Atividade.objects.create(
                ator=quem_aceitou,
                verbo=f'aceitou o pedido de amizade de {quem_enviou.username}'
            )