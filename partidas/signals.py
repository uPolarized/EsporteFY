from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from .models import Partida
from social.models import Atividade


# =============================================================
# 🟢 1. Criou uma partida
# =============================================================
@receiver(post_save, sender=Partida)
def criar_atividade_nova_partida(sender, instance, created, **kwargs):
    if not created:
        return

    Atividade.objects.create(
        ator=instance.organizador,
        verbo="criou",
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
    )


# =============================================================
# 🟡 2. Jogador entrou / saiu da partida (ManyToMany)
# =============================================================
@receiver(m2m_changed, sender=Partida.jogadores_confirmados.through)
def atividade_jogador_movimento(sender, instance, action, pk_set, **kwargs):

    ct = ContentType.objects.get_for_model(instance)

    # ➤ Entrou na partida
    if action == "post_add":
        for user_pk in pk_set:
            jogador = User.objects.get(pk=user_pk)
            
            # NÃO CRIA atividade "entrou" se é o criador
            # (já tem atividade "criou" do post_save)
            if jogador == instance.organizador:
                continue

            # Evita duplicações
            Atividade.objects.filter(
                ator=jogador,
                content_type=ct,
                object_id=instance.id,
                verbo="entrou"
            ).delete()

            Atividade.objects.create(
                ator=jogador,
                verbo="entrou",
                content_type=ct,
                object_id=instance.id,
            )

    # ➤ Saiu da partida
    elif action == "post_remove":
        for user_pk in pk_set:
            jogador = User.objects.get(pk=user_pk)

            # Evita duplicações
            Atividade.objects.filter(
                ator=jogador,
                content_type=ct,
                object_id=instance.id,
                verbo="saiu"
            ).delete()

            Atividade.objects.create(
                ator=jogador,
                verbo="saiu",
                content_type=ct,
                object_id=instance.id,
            )


# =============================================================
# 🔴 3. Quando a partida é excluída → limpar atividades
# =============================================================
@receiver(pre_delete, sender=Partida)
def remover_atividades_relacionadas(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)

    Atividade.objects.filter(
        content_type=ct,
        object_id=instance.id
    ).delete()
