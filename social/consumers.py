import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Mensagem, Conversa

notificacoes_ativas = {}  # exemplo: { (destinatario_id, remetente_username): timestamp }


class FeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("feed", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("feed", self.channel_name)

    async def nova_atividade(self, event):
        await self.send(text_data=event["data"])


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
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')

        if message:
            message_data = await self.save_message_and_get_data(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_data': message_data
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message_data']))

    @database_sync_to_async
    def save_message_and_get_data(self, message_content):
        outro_usuario = User.objects.get(username=self.outro_usuario_username)

        conversa_qs = Conversa.objects.filter(participantes=self.meu_usuario).filter(participantes=outro_usuario)
        if conversa_qs.exists():
            conversa = conversa_qs.first()
        else:
            conversa = Conversa.objects.create()
            conversa.participantes.add(self.meu_usuario, outro_usuario)

        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=self.meu_usuario,
            conteudo=message_content
        )

        timestamp_local = mensagem.timestamp.astimezone(timezone.get_current_timezone())
        return {
            'type': 'chat_message',
            'message': mensagem.conteudo,
            'username': mensagem.remetente.username,
            'user_avatar_url': (
                mensagem.remetente.perfil.foto.url
                if hasattr(mensagem.remetente, "perfil") and mensagem.remetente.perfil.foto
                else ""
            ),
            'timestamp': timestamp_local.strftime('%H:%M'),
        }


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f'notifications_user_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            try:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            except Exception as e:
                print(f"[DISCONNECT WARNING] Erro ao sair do grupo: {e}")

    # 🔔 Notificação genérica (amizades, partidas etc.)
    async def send_generic_notification(self, event):
        data = {
            'type': 'nova_atividade',
            'titulo': event.get('titulo', 'Nova atividade'),
            'mensagem': event.get('mensagem', ''),
        }

        # 🔗 Campos extras usados no frontend (amizade em tempo real)
        if 'acao' in event:
            data['acao'] = event['acao']
        if 'usuario_id' in event:
            data['usuario_id'] = event['usuario_id']
        if 'solicitacao_id' in event:
            data['solicitacao_id'] = event['solicitacao_id']
        if 'solicitante_id' in event:
            data['solicitante_id'] = event['solicitante_id']

        await self.send(text_data=json.dumps(data))

    # 💬 Notificação de mensagem
    async def send_notification(self, event):
        remetente = event['remetente']
        conversa_url = event['conversa_url']
        chave = (self.user.id, remetente)

        if chave in notificacoes_ativas:
            return

        notificacoes_ativas[chave] = True

        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'remetente': remetente,
            'conversa_url': conversa_url,
        }))

        await asyncio.sleep(5)
        notificacoes_ativas.pop(chave, None)
