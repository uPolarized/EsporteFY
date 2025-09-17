import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Mensagem, Conversa

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.outro_usuario_username = self.scope['url_route']['kwargs']['username']
        self.meu_usuario = self.scope['user']

        if not self.meu_usuario.is_authenticated:
            await self.close()
            return

        usernames = sorted([self.meu_usuario.username, self.outro_usuario_username])
        self.room_group_name = f'chat_{usernames[0]}_{usernames[1]}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(f"Desconectado do grupo '{self.room_group_name}' com o código: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        logger.info(f"Mensagem recebida de '{self.scope['user']}': {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        nova_mensagem = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': nova_mensagem.conteudo,
                'username': nova_mensagem.remetente.username,
                'timestamp': nova_mensagem.timestamp.strftime('%H:%M')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, message_content):
        outro_usuario = User.objects.get(username=self.outro_usuario_username)

        # Verifica se já existe conversa entre os dois usuários
        conversa = (
            Conversa.objects.filter(participantes=self.meu_usuario)
            .filter(participantes=outro_usuario)
            .first()
        )

        # Se não existe, cria uma nova
        if not conversa:
            conversa = Conversa.objects.create()
            conversa.participantes.add(self.meu_usuario, outro_usuario)

        # Salva a nova mensagem
        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=self.meu_usuario,
            conteudo=message_content
        )
        return mensagem
    
# --- NOVO CONSUMER PARA NOTIFICAÇÕES GLOBAIS ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        # Cada utilizador entra num grupo individual
        self.room_group_name = f'notifications_user_{self.user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Função que é chamada para enviar a notificação para o frontend
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'remetente': event['remetente'],
            'conversa_url': event['conversa_url'],
        }))
