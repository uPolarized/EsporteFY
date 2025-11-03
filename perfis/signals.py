from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from social.models import Atividade


@receiver(m2m_changed, sender=Perfil.amigos.through)
def criar_atividade_nova_amizade(sender, instance, action, pk_set, **kwargs):
    """
    Cria apenas uma atividade única quando uma nova amizade é formada.
    Evita duplicar o evento para os dois perfis.
    """
    if action == 'post_add':
        quem_aceitou = instance.user

        for user_pk in pk_set:
            quem_enviou = User.objects.get(pk=user_pk)

            # 🔒 Verifica se já existe amizade mútua — só cria a atividade uma vez
            if not Atividade.objects.filter(
                ator__in=[quem_aceitou, quem_enviou],
                verbo__icontains="agora são amigos"
            ).exists():
                Atividade.objects.create(
                    ator=quem_aceitou,
                    verbo=f"{quem_aceitou.username} e {quem_enviou.username} agora são amigos!"
                )
