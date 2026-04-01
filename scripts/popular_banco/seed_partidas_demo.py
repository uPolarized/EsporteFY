from datetime import datetime, timedelta
import random

from django.contrib.auth.models import User
from django.utils import timezone

from partidas.models import Partida, Esporte
from quadras.models import Quadra


def _build_slot(day_offset: int, hour: int, minute: int = 0):
    base_date = timezone.localdate() + timedelta(days=day_offset)
    naive = datetime(base_date.year, base_date.month, base_date.day, hour, minute)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def run(organizer_username='JoaoVictorzz', seed_value=42):
    organizer = User.objects.filter(username__iexact=organizer_username).first()
    if not organizer:
        return {
            'ok': False,
            'message': f"Usuario '{organizer_username}' nao encontrado.",
            'created': 0,
            'created_ids': [],
        }

    esportes = list(Esporte.objects.order_by('nome'))
    quadras = list(Quadra.objects.order_by('nome'))
    outros = list(User.objects.exclude(id=organizer.id).order_by('id'))

    if not esportes or not quadras:
        return {
            'ok': False,
            'message': 'Esportes/Quadras vazios. Rode os seeds antes.',
            'created': 0,
            'created_ids': [],
        }

    random.seed(seed_value)

    titulos = [
        'Pelada da Resenha',
        'Clube da Virada',
        'Noite do Contra-ataque',
        'Quarta do Toque de Bola',
        'Racha dos Brabos',
        'Bola na Rede Express',
        'Partida do Fair Play',
        'Desafio do Meio-Campo',
        'Jogo da Virada Relampago',
        'Copa da Mumbuca',
        'Sextou na Quadra',
        'Fut do Por do Sol',
        'Treino de Fundamentos',
        'Partida Open da Cidade',
        'Amistoso da Galera',
        'Aquecimento da Semana',
        'Classico de Bairro',
        'Ritmo de Jogo',
        'Noite do Tabelinha',
        'Liga da Comunidade',
        'Racha de Quinta',
        'Ataque Total',
        'Duelo das Estrelas',
        'Encontro da Bola',
        'Bola e Resenha Premium',
        'Partida da Rodada',
        'Noite da Pressao Alta',
        'Jogo dos Amigos',
        'Partida Flash',
        'Copa Relampago Local',
    ]

    weekday_slots = [(19, 0), (20, 30), (21, 30)]
    weekend_slots = [(8, 0), (9, 30), (16, 0), (18, 0)]

    created_ids = []

    for i, titulo in enumerate(titulos):
        day_offset = i + 1
        target_date = timezone.localdate() + timedelta(days=day_offset)
        is_weekend = target_date.weekday() >= 5
        hour, minute = random.choice(weekend_slots if is_weekend else weekday_slots)
        data_hora = _build_slot(day_offset, hour, minute)

        esporte = esportes[i % len(esportes)]
        quadra = quadras[(i * 3) % len(quadras)]
        jogadores_necessarios = random.choice([8, 10, 12])

        partida = Partida.objects.create(
            organizador=organizer,
            titulo=titulo,
            esporte=esporte,
            quadra=quadra,
            data_hora=data_hora,
            jogadores_necessarios=jogadores_necessarios,
        )

        if outros:
            modo = random.choice(['aberta', 'quase', 'lotada'])
            if modo == 'aberta':
                qtd = random.randint(0, max(0, jogadores_necessarios // 3))
            elif modo == 'quase':
                qtd = max(0, jogadores_necessarios - random.randint(1, 3))
            else:
                qtd = jogadores_necessarios

            qtd = min(qtd, len(outros))
            if qtd > 0:
                participantes = random.sample(outros, qtd)
                partida.jogadores_confirmados.add(*participantes)

        created_ids.append(partida.id)

    total_usuario = Partida.objects.filter(organizador=organizer).count()

    return {
        'ok': True,
        'message': 'Partidas seed executadas com sucesso.',
        'created': len(created_ids),
        'created_ids': created_ids,
        'organizer': organizer.username,
        'total_organizer_matches': total_usuario,
    }
