from django.core.management import call_command
from django.core.management.base import BaseCommand

from scripts.popular_banco.configurar_social_google import run as run_social_google
from scripts.popular_banco.criar_superusuario_padrao import run as run_superuser
from scripts.popular_banco.seed_partidas_demo import run as run_seed_partidas


class Command(BaseCommand):
    help = 'Executa todos os passos de populacao de banco em um comando.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sem-partidas',
            action='store_true',
            help='Nao cria partidas de demonstracao.',
        )
        parser.add_argument(
            '--organizador',
            default='JoaoVictorzz',
            help='Username organizador para seed de partidas (default: JoaoVictorzz).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando populacao completa do banco...'))

        self.stdout.write('1/4 Seed de esportes...')
        call_command('seed_esporte')

        self.stdout.write('2/4 Seed de quadras...')
        call_command('seed_quadras')

        self.stdout.write('3/4 Criacao/atualizacao de superusuario padrao...')
        su_result = run_superuser()
        if su_result['created']:
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{su_result['username']}' criado."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{su_result['username']}' atualizado."))

        self.stdout.write('4/4 Configuracao do Google SocialApp...')
        social_result = run_social_google()
        if social_result['created']:
            self.stdout.write(self.style.SUCCESS('Google SocialApp criada.'))
        else:
            self.stdout.write(self.style.SUCCESS('Google SocialApp ja existia.'))

        if not options['sem_partidas']:
            self.stdout.write('Extra: Seed de partidas demo...')
            partidas_result = run_seed_partidas(organizer_username=options['organizador'])
            if partidas_result['ok']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{partidas_result['created']} partidas criadas para {partidas_result['organizer']}."
                    )
                )
            else:
                self.stdout.write(self.style.WARNING(f"Seed de partidas ignorada: {partidas_result['message']}"))

        self.stdout.write(self.style.SUCCESS('Populacao finalizada.'))
        self.stdout.write('Comando unico para o time: python manage.py popular_banco')
