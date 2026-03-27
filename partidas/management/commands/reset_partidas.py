from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from partidas.models import Partida, Esporte
from quadras.models import Quadra


class Command(BaseCommand):
    help = 'Reset partidas e cria 10 novas partidas para um usuário específico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nome de usuário que será o organizador das partidas')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuário "{username}" não encontrado'))
            return
        
        # 1. Deletar todas as partidas
        total_deletadas = Partida.objects.count()
        Partida.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Deletadas {total_deletadas} partidas'))
        
        # 2. Pegar esportes e quadras
        esportes = list(Esporte.objects.all())
        quadras = list(Quadra.objects.all())
        
        if not esportes:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum esporte cadastrado. Criando esportes padrão...'))
            esportes = [
                Esporte.objects.create(nome='Futebol'),
                Esporte.objects.create(nome='Futsal'),
                Esporte.objects.create(nome='Vôlei'),
                Esporte.objects.create(nome='Basquete'),
            ]
        
        if not quadras:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma quadra cadastrada. Criando quadras padrão...'))
            # Você precisaria de Bairro model aqui, mas vou criar sem bairro por hora
            quadras = [
                Quadra.objects.create(nome='Quadra Centro', endereco='Av. Principal, 100'),
                Quadra.objects.create(nome='Quadra Zona Sul', endereco='Rua da Paz, 200'),
                Quadra.objects.create(nome='Quadra Zona Norte', endereco='Av. Paulista, 300'),
            ]
        
        # 3. Criar 10 partidas
        nomes_partidas = [
            'Bola e Resenha Premium',
            'Encontro da Bola',
            'Jogo Rápido',
            'Pelada do Bairro',
            'Campeonato Amigável',
            'Jogo Noturno',
            'Torneio Flash',
            'Desafio Esportivo',
            'Ida e Volta',
            'Clássico do Futebol',
        ]
        
        now = timezone.now()
        criadas = 0
        
        for i, nome in enumerate(nomes_partidas):
            data_partida = now + timedelta(days=i+1, hours=18)
            esporte = esportes[i % len(esportes)]
            quadra = quadras[i % len(quadras)]
            
            partida = Partida.objects.create(
                organizador=user,
                titulo=nome,
                esporte=esporte,
                quadra=quadra,
                data_hora=data_partida,
                jogadores_necessarios=10 + (i % 5)
            )
            
            # Adicionar o organizador como confirmado
            partida.jogadores_confirmados.add(user)
            
            criadas += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ [{criadas}/10] {nome} | {data_partida.strftime("%d/%m %H:%M")} | {quadra.nome}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 {criadas} partidas criadas para {user.username}!'))
