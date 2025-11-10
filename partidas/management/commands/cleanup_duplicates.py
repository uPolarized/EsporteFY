from django.core.management.base import BaseCommand
from social.models import Atividade
from partidas.models import Partida
from django.db.models import Count


class Command(BaseCommand):
    help = "Remove duplicadas do feed e partidas duplicadas no banco."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🧹 Limpando duplicadas de Partidas e Atividades..."))

        total_partidas_removidas = 0
        total_atividades_removidas = 0

        # === LIMPAR PARTIDAS DUPLICADAS ===
        duplicadas_partidas = (
            Partida.objects.values("titulo", "quadra", "data_hora", "organizador")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        for grupo in duplicadas_partidas:
            partidas = (
                Partida.objects.filter(
                    titulo=grupo["titulo"],
                    quadra=grupo["quadra"],
                    data_hora=grupo["data_hora"],
                    organizador=grupo["organizador"],
                )
                .order_by("-id")
            )
            extras = list(partidas)[1:]
            for extra in extras:
                extra.delete()
                total_partidas_removidas += 1

        # === LIMPAR ATIVIDADES DUPLICADAS ===
        duplicadas_feed = (
            Atividade.objects.values("ator", "content_type", "object_id")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        for grupo in duplicadas_feed:
            atividades = (
                Atividade.objects.filter(
                    ator=grupo["ator"],
                    content_type=grupo["content_type"],
                    object_id=grupo["object_id"],
                )
                .order_by("-timestamp")
            )
            extras = list(atividades)[1:]
            for extra in extras:
                extra.delete()
                total_atividades_removidas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {total_partidas_removidas} partidas e {total_atividades_removidas} atividades duplicadas removidas."
            )
        )
