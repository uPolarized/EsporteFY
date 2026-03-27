from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from partidas.models import Partida
from social.models import Atividade


class Command(BaseCommand):
    help = "Remove atividades órfãs (apontando para partidas deletadas)"

    def handle(self, *args, **options):
        # Pega o ContentType de Partida
        ct_partida = ContentType.objects.get_for_model(Partida)

        # Encontra atividades de Partida
        atividades_partida = Atividade.objects.filter(content_type=ct_partida)

        deletados = 0
        for atividade in atividades_partida:
            try:
                # Tenta buscar a Partida
                partida = Partida.objects.get(id=atividade.object_id)
            except Partida.DoesNotExist:
                # Partida não existe = atividade órfã
                self.stdout.write(
                    self.style.WARNING(
                        f"🪦 Deletando atividade órfã: {atividade.ator.username} {atividade.verbo} (Partida ID: {atividade.object_id})"
                    )
                )
                atividade.delete()
                deletados += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Total de atividades órfãs removidas: {deletados}")
        )
