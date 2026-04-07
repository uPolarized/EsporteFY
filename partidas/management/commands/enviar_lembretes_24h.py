from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from partidas.models import Partida, PartidaRSVP
from app.redis_utils import publish_to_redis

class Command(BaseCommand):
    help = 'Envia notificações para usuários confirmarem presença em partidas que ocorrerão em 24h ou que precisam ser aprovados.'

    def handle(self, *args, **kwargs):
        agora = timezone.now()
        daqui_a_24h_inicio = agora + timedelta(hours=23, minutes=30)
        daqui_a_24h_fim = agora + timedelta(hours=24, minutes=30)

        # Encontrar todas as partidas agendadas para daqui a aproximadamente 24 horas
        partidas_em_24h = Partida.objects.filter(
            data_hora__range=(daqui_a_24h_inicio, daqui_a_24h_fim)
        )

        n_lembretes = 0
        for partida in partidas_em_24h:
            # Buscar RSVPs do tipo INTERESSE (onde o usuário tem interesse mas ainda não confirmou/pagou/etc)
            # Para os quais não enviamos lembrete ainda
            rsvps_interesse = PartidaRSVP.objects.filter(
                partida=partida,
                status=PartidaRSVP.STATUS_INTERESSE,
                lembrete_24h_enviado=False
            ).select_related('jogador', 'jogador__perfil')

            for rsvp in rsvps_interesse:
                # Criar e disparar notificação socket
                user = rsvp.jogador
                msg_notificacao = f'A partida "{partida.titulo}" acontece em 24 horas! Confirme sua presença agora mesmo.'
                
                try:
                    payload = {
                        'type': 'send_generic_notification',
                        'remetente': 'Equipe EsporteFY',
                        'mensagem': msg_notificacao,
                        'foto_url': '/static/images/logo_icon.png', # Caso tenha uma logo padrão
                        'timestamp': 'agora',
                        'conversa_url': f'/partidas/{partida.id}/' 
                    }
                    publish_to_redis(f'notifications_user_{user.id}', payload)
                    rsvp.lembrete_24h_enviado = True
                    rsvp.save(update_fields=['lembrete_24h_enviado'])
                    n_lembretes += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Erro ao enviar lembrete para {user.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Comando concluído. {n_lembretes} lembretes de 24h enviados.'))