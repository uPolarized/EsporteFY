import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache  # <--- IMPORTANTE
from .models import Mensagem, Conversa

# Removemos a variável global notificacoes_ativas

class FeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("feed", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("feed", self.channel_name)

    async def nova_atividade(self, event):
        # Envia o payload exato que veio do signal/view
        await self.send(text_data=event["data"])


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Pega o nome da sala da URL (definido no routing.py)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
        else:
            # Entra no grupo do chat
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        # Sai do grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 1. Recebe a mensagem do WebSocket (do JavaScript)
    async def receive(self, text_data):
        text_data_json = json.load(text_data)
        mensagem_texto = text_data_json['mensagem']
        
        # Salva no banco de dados (função auxiliar abaixo)
        nova_mensagem = await self.save_message(mensagem_texto)

        if nova_mensagem:
            # 2. Envia a mensagem para o GRUPO (broadcast)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', # Chama o método abaixo
                    'message': mensagem_texto,
                    'username': self.user.username,
                    'user_id': self.user.id,
                    # Se tiver foto, mande a URL, senão vazio
                    'foto_url': nova_mensagem.remetente.perfil.foto.url if hasattr(nova_mensagem.remetente, 'perfil') and nova_mensagem.remetente.perfil.foto else "",
                    'timestamp': nova_mensagem.timestamp.strftime('%H:%M')
                }
            )

    # 3. Recebe do GRUPO e envia de volta para o WebSocket (para o JavaScript)
    async def chat_message(self, event):
        # Envia JSON final para o frontend
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'foto_url': event['foto_url'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, texto):
        # Lógica para encontrar a conversa e salvar
        try:
            # Aqui assumimos que self.room_name é o ID da conversa ou algo único
            # Se sua URL for /chat/<username>/, precisamos ajustar essa lógica.
            # O ideal para chat real-time é usar o ID da Conversa na URL do WebSocket.
            
            # Tenta buscar conversa pelo ID (se room_name for numérico)
            if self.room_name.isdigit():
                conversa = Conversa.objects.get(id=int(self.room_name))
            else:
                # Fallback ou lógica customizada se room_name for string
                return None
                
            mensagem = Mensagem.objects.create(
                conversa=conversa,
                remetente=self.user,
                conteudo=texto
            )
            return mensagem
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")
            return None


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Grupo único do usuário
        self.room_group_name = f'notifications_user_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # 🔔 Notificação genérica
    async def send_generic_notification(self, event):
        # Monta o dicionário base
        data = {
            'type': 'nova_atividade',
            'titulo': event.get('titulo', 'Nova atividade'),
            'mensagem': event.get('mensagem', ''),
        }
        
        # Adiciona campos extras dinamicamente se existirem no evento
        campos_extras = ['acao', 'usuario_id', 'solicitacao_id', 'solicitante_id', 'foto_url']
        for campo in campos_extras:
            if campo in event:
                data[campo] = event[campo]

        await self.send(text_data=json.dumps(data))

    # No NotificationConsumer dentro de consumers.py

    # 💬 Notificação de mensagem (CORRIGIDO)
    async def send_notification(self, event):
        remetente = event['remetente']
        conversa_url = event['conversa_url']
        
        # Pega a mensagem e a foto que vieram do signal
        mensagem_texto = event.get('mensagem', 'Nova mensagem')
        foto_url = event.get('foto_url', '')

        # Chave para o debounce (evita notificação duplicada em 5s)
        cache_key = f"notif_msg_{self.user.id}_{remetente}"

        if await database_sync_to_async(cache.get)(cache_key):
            return

        await database_sync_to_async(cache.set)(cache_key, "true", 5)

        # AQUI ESTAVA O PROBLEMA: Faltava enviar a foto e a mensagem no JSON final
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification', # O JS vai procurar por esse nome exato
            'remetente': remetente,
            'mensagem': mensagem_texto,         # Enviando o texto
            'foto_url': foto_url,               # Enviando a foto
            'conversa_url': conversa_url,
        }))