from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from app.redis_utils import publish_to_redis
from social.models import Atividade

from .models import Partida


def _build_notification_payload(partida, remetente, foto_url):
    return {
        "type": "notification",
        "remetente": remetente,
        "foto_url": foto_url,
        "mensagem": f"a partida '{partida.titulo}' foi finalizada.",
        "conversa_url": "/feed/",
        "timestamp": "agora",
    }


def processar_partidas_finalizadas():
    """
    Remove do feed atividades de partidas que ja passaram do horario e
    envia notificacao para quem participou da partida.
    """
    ct_partida = ContentType.objects.get_for_model(Partida)

    atividade_qs = Atividade.objects.filter(
        content_type=ct_partida,
        verbo__in=["criou", "entrou", "saiu"],
        object_id__isnull=False,
    )

    partida_ids = list(atividade_qs.values_list("object_id", flat=True).distinct())
    if not partida_ids:
        return {"partidas_finalizadas": 0, "atividades_removidas": 0, "notificacoes_enviadas": 0}

    partidas_finalizadas = list(
        Partida.objects.filter(id__in=partida_ids, data_hora__lt=timezone.now())
        .select_related("organizador")
        .prefetch_related("jogadores_confirmados")
    )

    if not partidas_finalizadas:
        return {"partidas_finalizadas": 0, "atividades_removidas": 0, "notificacoes_enviadas": 0}

    notificacoes_enviadas = 0
    atividades_removidas = 0

    for partida in partidas_finalizadas:
        foto_url = "/media/fotos_perfil/default.jpg"
        if hasattr(partida.organizador, "perfil") and getattr(partida.organizador.perfil, "foto", None):
            try:
                foto_url = partida.organizador.perfil.foto.url
            except Exception:
                pass

        participantes = list(partida.jogadores_confirmados.all())
        for participante in participantes:
            publish_to_redis(
                f"notifications_user_{participante.id}",
                _build_notification_payload(partida, partida.organizador.username, foto_url),
            )
            notificacoes_enviadas += 1

        deleted_count, _ = Atividade.objects.filter(
            content_type=ct_partida,
            object_id=partida.id,
            verbo__in=["criou", "entrou", "saiu"],
        ).delete()
        atividades_removidas += deleted_count

    return {
        "partidas_finalizadas": len(partidas_finalizadas),
        "atividades_removidas": atividades_removidas,
        "notificacoes_enviadas": notificacoes_enviadas,
    }
