from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import Partida
from social.models import Atividade


# ---------------------------------------------------------
# 🟢 Quando uma nova partida é criada
# ---------------------------------------------------------
@receiver(post_save, sender=Partida)
def criar_atividade_nova_partida(sender, instance, created, **kwargs):
    if not created:
        return

    content_type = ContentType.objects.get_for_model(instance)

    # Evita duplicar a criação
    existe = Atividade.objects.filter(
        ator=instance.organizador,
        verbo__icontains="criou",
        content_type=content_type,
        object_id=instance.id,
    ).exists()

    if not existe:
        Atividade.objects.create(
            ator=instance.organizador,
            verbo="criou uma nova partida",
            content_type=content_type,
            object_id=instance.id,
        )


# ---------------------------------------------------------
# 🟡 Quando um jogador entra numa partida
# ---------------------------------------------------------
@receiver(m2m_changed, sender=Partida.jogadores_confirmados.through)
def criar_atividade_novo_jogador(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        content_type = ContentType.objects.get_for_model(instance)

        for user_pk in pk_set:
            jogador = User.objects.get(pk=user_pk)

            # Evita duplicar o organizador
            if jogador != instance.organizador:
                Atividade.objects.create(
                    ator=jogador,
                    verbo='entrou na partida',
                    content_type=content_type,
                    object_id=instance.id,
                )
