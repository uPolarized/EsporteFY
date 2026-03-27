from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from partidas.models import Partida
from social.models import Atividade


class Command(BaseCommand):
    help = "Remove atividades duplicadas de 'entrou' onde o ator é o organizador da partida"

    def handle(self, *args, **options):
        # Pega o ContentType de Partida
        ct_partida = ContentType.objects.get_for_model(Partida)

        # Encontra atividades onde:
        # - verbo = "entrou"
        # - content_type = Partida
        # - ator = organizador da partida
        atividades_duplicadas = Atividade.objects.filter(
            verbo="entrou",
            content_type=ct_partida,
        )

        deletados = 0
        for atividade in atividades_duplicadas:
            try:
                # Pega a partida relacionada
                partida = Partida.objects.get(id=atividade.object_id)
                
                # Se o ator é o organizador, deleta (é duplicada)
                if atividade.ator == partida.organizador:
                    atividade.delete()
                    deletados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"❌ Deletado: {atividade.ator.username} entrou em {partida} (duplicado com 'criou')"
                        )
                    )
            except Partida.DoesNotExist:
                # Se a partida não existe, deleta também
                atividade.delete()
                deletados += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Deletado: {atividade.ator.username} - Partida não encontrada"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Total de atividades duplicadas removidas: {deletados}")
        )
