import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Mensagem, Conversa

notificacoes_ativas = {}  # exemplo: { (destinatario_id, remetente_username): timestamp }

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
        # Adicione esta verificação (if hasattr...)
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name, 
                self.channel_name
            )

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
        message_data = event['message_data']
        await self.send(text_data=json.dumps(message_data))

    # --- FUNÇÃO ATUALIZADA E SIMPLIFICADA ---
    @database_sync_to_async
    def save_message_and_get_data(self, message_content):
        outro_usuario = User.objects.get(username=self.outro_usuario_username)
        
        # Procura por uma conversa que contenha ambos os utilizadores.
        # Esta é uma forma mais robusta de encontrar a conversa correta.
        conversa_qs = Conversa.objects.filter(
            participantes=self.meu_usuario
        ).filter(
            participantes=outro_usuario
        )

        if conversa_qs.exists():
            conversa = conversa_qs.first()
        else:
            # Se não existir, cria uma nova e adiciona os dois participantes.
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
            'user_avatar_url': mensagem.remetente.perfil.foto.url,
            'timestamp': timestamp_local.strftime('%H:%M'),
        }
# --- Consumer para Notificações Globais ---
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
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_notification(self, event):
        """Evita spam de notificações idênticas em sequência"""
        remetente = event['remetente']
        conversa_url = event['conversa_url']
        chave = (self.user.id, remetente)  # identifica o par usuário→remetente

        # Verifica se já existe uma notificação ativa desse remetente para este usuário
        if chave in notificacoes_ativas:
            # Ignora se a notificação ainda está dentro do período de cooldown
            return

        # Marca como ativa
        notificacoes_ativas[chave] = True

        # Envia a notificação para o frontend
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'remetente': remetente,
            'conversa_url': conversa_url,
        }))

        # Espera alguns segundos antes de permitir nova notificação do mesmo remetente
        await asyncio.sleep(5)
        notificacoes_ativas.pop(chave, None)