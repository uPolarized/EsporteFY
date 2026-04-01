from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Partida
from social.models import Atividade
from app.redis_utils import publish_to_redis


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

            if instance.organizador_id != jogador.id:
                foto_url = jogador.perfil.foto.url if hasattr(jogador, 'perfil') and jogador.perfil.foto else "/media/fotos_perfil/default.jpg"
                publish_to_redis(
                    f"notifications_user_{instance.organizador_id}",
                    {
                        "type": "notification",
                        "remetente": jogador.username,
                        "foto_url": foto_url,
                        "mensagem": f"confirmou presença na sua partida '{instance.titulo}'.",
                        "conversa_url": "/feed/",
                        "timestamp": "agora",
                        "timestamp_iso": timezone.now().isoformat(),
                    },
                )

            # Também notifica o próprio jogador para preencher o histórico dele.
            my_foto_url = instance.organizador.perfil.foto.url if hasattr(instance.organizador, 'perfil') and instance.organizador.perfil.foto else "/media/fotos_perfil/default.jpg"
            publish_to_redis(
                f"notifications_user_{jogador.id}",
                {
                    "type": "notification",
                    "remetente": instance.organizador.username,
                    "foto_url": my_foto_url,
                    "mensagem": f"Sua inscrição em '{instance.titulo}' foi confirmada.",
                    "conversa_url": "/feed/",
                    "timestamp": "agora",
                    "timestamp_iso": timezone.now().isoformat(),
                },
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

            if instance.organizador_id != jogador.id:
                foto_url = jogador.perfil.foto.url if hasattr(jogador, 'perfil') and jogador.perfil.foto else "/media/fotos_perfil/default.jpg"
                publish_to_redis(
                    f"notifications_user_{instance.organizador_id}",
                    {
                        "type": "notification",
                        "remetente": jogador.username,
                        "foto_url": foto_url,
                        "mensagem": f"cancelou a presença na sua partida '{instance.titulo}'.",
                        "conversa_url": "/feed/",
                        "timestamp": "agora",
                        "timestamp_iso": timezone.now().isoformat(),
                    },
                )

            # Também notifica o próprio jogador para preencher o histórico dele.
            my_foto_url = instance.organizador.perfil.foto.url if hasattr(instance.organizador, 'perfil') and instance.organizador.perfil.foto else "/media/fotos_perfil/default.jpg"
            publish_to_redis(
                f"notifications_user_{jogador.id}",
                {
                    "type": "notification",
                    "remetente": instance.organizador.username,
                    "foto_url": my_foto_url,
                    "mensagem": f"Sua inscrição em '{instance.titulo}' foi cancelada.",
                    "conversa_url": "/feed/",
                    "timestamp": "agora",
                    "timestamp_iso": timezone.now().isoformat(),
                },
            )


# =============================================================
# 🔴 3. Quando a partida é excluída → limpar atividades
# =============================================================
@receiver(pre_delete, sender=Partida)
def remover_atividades_relacionadas(sender, instance, **kwargs):
    ct = ContentType.objects.get_for_model(instance)

    try:
        foto_url = instance.organizador.perfil.foto.url if hasattr(instance.organizador, 'perfil') and instance.organizador.perfil.foto else "/media/fotos_perfil/default.jpg"
        for jogador in instance.jogadores_confirmados.all():
            if jogador.id != instance.organizador_id:
                publish_to_redis(
                    f"notifications_user_{jogador.id}",
                    {
                        "type": "notification",
                        "remetente": instance.organizador.username,
                        "foto_url": foto_url,
                        "mensagem": f"cancelou a partida '{instance.titulo}'.",
                        "conversa_url": "/feed/",
                        "timestamp": "agora",
                        "timestamp_iso": timezone.now().isoformat(),
                    },
                )
    except Exception:
        pass

    Atividade.objects.filter(
        content_type=ct,
        object_id=instance.id
    ).delete()
