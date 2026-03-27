from datetime import datetime, timedelta
import random

import django
from django.utils import timezone


django.setup()

from django.contrib.auth.models import User
from partidas.models import Partida, Esporte
from quadras.models import Quadra


def build_slot(day_offset: int, hour: int, minute: int = 0):
    base_date = timezone.localdate() + timedelta(days=day_offset)
    naive = datetime(base_date.year, base_date.month, base_date.day, hour, minute)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def main():
    organizer = User.objects.filter(username__iexact="JoaoVictorzz").first()
    if not organizer:
        print("ERRO: Usuario 'JoaoVictorzz' nao encontrado.")
        return

    esportes = list(Esporte.objects.order_by("nome"))
    quadras = list(Quadra.objects.order_by("nome"))
    outros = list(User.objects.exclude(id=organizer.id).order_by("id"))

    if not esportes or not quadras:
        print("ERRO: Esportes/Quadras vazios. Rode os seeds antes.")
        return

    random.seed(42)

    titulos = [
        "Pelada da Resenha",
        "Clube da Virada",
        "Noite do Contra-ataque",
        "Quarta do Toque de Bola",
        "Racha dos Brabos",
        "Bola na Rede Express",
        "Partida do Fair Play",
        "Desafio do Meio-Campo",
        "Jogo da Virada Relampago",
        "Copa da Mumbuca",
        "Sextou na Quadra",
        "Fut do Por do Sol",
        "Treino de Fundamentos",
        "Partida Open da Cidade",
        "Amistoso da Galera",
        "Aquecimento da Semana",
        "Classico de Bairro",
        "Ritmo de Jogo",
        "Noite do Tabelinha",
        "Liga da Comunidade",
        "Racha de Quinta",
        "Ataque Total",
        "Duelo das Estrelas",
        "Encontro da Bola",
        "Bola e Resenha Premium",
        "Partida da Rodada",
        "Noite da Pressao Alta",
        "Jogo dos Amigos",
        "Partida Flash",
        "Copa Relampago Local",
    ]

    # Horarios realistas: noite em dias uteis e manha/tarde no fim de semana.
    weekday_slots = [(19, 0), (20, 30), (21, 30)]
    weekend_slots = [(8, 0), (9, 30), (16, 0), (18, 0)]

    created = 0
    created_ids = []

    for i, titulo in enumerate(titulos):
        day_offset = i + 1  # evita datas passadas para aparecer em "Partidas abertas"
        target_date = timezone.localdate() + timedelta(days=day_offset)
        is_weekend = target_date.weekday() >= 5
        hour, minute = random.choice(weekend_slots if is_weekend else weekday_slots)
        data_hora = build_slot(day_offset, hour, minute)

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

        # Simula ocupacao variada: algumas quase lotadas, algumas lotadas, outras abertas.
        if outros:
            modo = random.choice(["aberta", "quase", "lotada"])
            if modo == "aberta":
                qtd = random.randint(0, max(0, jogadores_necessarios // 3))
            elif modo == "quase":
                qtd = max(0, jogadores_necessarios - random.randint(1, 3))
            else:
                qtd = jogadores_necessarios

            qtd = min(qtd, len(outros))
            if qtd > 0:
                participantes = random.sample(outros, qtd)
                partida.jogadores_confirmados.add(*participantes)

        created += 1
        created_ids.append(partida.id)

    total_usuario = Partida.objects.filter(organizador=organizer).count()
    print(f"OK: {created} partidas criadas para {organizer.username}.")
    print(f"Total de partidas desse usuario: {total_usuario}.")
    print(f"IDs novas: {created_ids[:10]}{'...' if len(created_ids) > 10 else ''}")


if __name__ == "__main__":
    main()
