# SEU_APP/management/commands/seed_esportes.py
from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Esporte  # ajuste o import conforme o local do modelo




ESPORTES = [
    "Futebol",
    "Futsal",
    "Basquete",
    "Vôlei",
    "Tênis",
    "Handebol",
    "Queimada",
]


class Command(BaseCommand):
    help = "Popula o banco com esportes básicos (seed)."

    @transaction.atomic
    def handle(self, *args, **options):
        created, skipped = 0, 0

        for nome in ESPORTES:
            nome = nome.strip()
            if not Esporte.objects.filter(nome__iexact=nome).exists():
                Esporte.objects.create(nome=nome)
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed de esportes finalizado. Criados: {created} | Já existiam: {skipped}"
            )
        )


class Command(BaseCommand):
    help = "Popula o banco com esportes básicos (seed)."
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Remove esportes antigos e sincroniza apenas com os listados.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["sync"]:
            self.stdout.write("⚠️ Limpando esportes antigos...")
            Esporte.objects.all().delete()

        created, skipped = 0, 0
        for nome in ESPORTES:
            nome = nome.strip()
            obj, created_flag = Esporte.objects.get_or_create(nome__iexact=nome, defaults={"nome": nome})
            if created_flag:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed de esportes finalizado. Criados: {created} | Já existiam: {skipped}"
            )
        )
