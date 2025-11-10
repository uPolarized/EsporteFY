from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import Partida
from social.models import Atividade

@receiver(post_save, sender=Partida)
def criar_atividade_nova_partida(sender, instance, created, **kwargs):
    if not created:
        return

    from social.models import Atividade
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(instance)

    # evita duplicar a criação
    existe = Atividade.objects.filter(
        ator=instance.organizador,
        verbo__icontains="criou",
        content_type=content_type,
        object_id=instance.id,
    ).exists()

    if not existe:
        Atividade.objects.create(
            ator=instance.organizador,
            verbo="criou uma nova partida",  # 👈 apenas o texto base
            alvo=instance,  # 👈 o template renderiza o título
        )


@receiver(m2m_changed, sender=Partida.jogadores_confirmados.through)
def criar_atividade_novo_jogador(sender, instance, action, pk_set, **kwargs):
    """
    Cria uma atividade sempre que um novo jogador entra numa partida.
    """
    # 'post_add' significa que um ou mais jogadores foram adicionados
    if action == 'post_add':
        # pk_set contém os IDs dos jogadores que acabaram de ser adicionados
        for user_pk in pk_set:
            jogador = User.objects.get(pk=user_pk)
            
            # Não cria uma atividade para o organizador, pois ele já entra ao criar
            if jogador != instance.organizador:
                Atividade.objects.create(
                    ator=jogador,
                    verbo='entrou na partida',
                    alvo=instance
                )