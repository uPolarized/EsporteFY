import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Mensagem, Conversa

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
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        is_typing = data.get('is_typing')

        if message:
            # A função save_message_and_get_data já prepara o "pacote" completo
            message_data = await self.save_message_and_get_data(message)
            
            # Envia o pacote para o grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_data': message_data
                }
            )
        
        elif is_typing is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': self.meu_usuario.username,
                    'is_typing': is_typing
                }
            )

    async def chat_message(self, event):
        # Pega o pacote de dados de dentro do evento
        message_data = event['message_data']
        # Envia o pacote completo para o JavaScript
        await self.send(text_data=json.dumps(message_data))

    async def typing_status(self, event):
        # Envia o status de "a digitar" para o JavaScript
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message_and_get_data(self, message_content):
        outro_usuario = User.objects.get(username=self.outro_usuario_username)
        conversa, _ = Conversa.objects.filter(participantes=self.meu_usuario).filter(participantes=outro_usuario).get_or_create()
        
        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=self.meu_usuario,
            conteudo=message_content
        )
        
        timestamp_local = mensagem.timestamp.astimezone(timezone.get_current_timezone())
        
        # Prepara o "pacote" completo de dados para o frontend
        return {
            'type': 'chat_message',
            'message': mensagem.conteudo,
            'username': mensagem.remetente.username,
            'user_avatar_url': mensagem.remetente.perfil.foto.url,
            'timestamp': timestamp_local.strftime('%H:%M'),
        }
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
