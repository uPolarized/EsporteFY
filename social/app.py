import json
import asyncio
import os
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from django.apps import AppConfig

# URL do Redis (compartilhado entre Django e o chat)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="EsporteFY Chat WebSocket")

# --- Permissões CORS (para ngrok, localhost, etc.) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja a domínios confiáveis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social'

    def ready(self):
        import social.signals

# === GERENCIADOR DE CONEXÕES ===
class ConnectionManager:
    """Gerencia conexões WebSocket por sala"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.redis = None

    async def connect(self, websocket: WebSocket, room: str):
        """Aceita a conexão e adiciona o socket à sala"""
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        """Remove o socket da sala"""
        if room in self.active_connections:
            self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def broadcast_local(self, room: str, message: dict):
        """Envia mensagem a todos os sockets conectados localmente"""
        if room in self.active_connections:
            for ws in self.active_connections[room]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


# === EVENTO DE INICIALIZAÇÃO ===
@app.on_event("startup")
async def startup_event():
    """Conecta ao Redis e inicia o listener de mensagens"""
    manager.redis = await redis.from_url(REDIS_URL, decode_responses=True)
    asyncio.create_task(redis_listener())


async def redis_listener():
    """Escuta mensagens publicadas no Redis e repassa aos WebSockets"""
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("chat_*")

    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            try:
                data = json.loads(message["data"])
                room = message["channel"]
                await manager.broadcast_local(room, data)
            except Exception as e:
                print(f"⚠️ Erro ao repassar mensagem Redis: {e}")


# === CHAT SOCKET ===
@app.websocket("/ws/chat/{username}/")
async def chat_socket(websocket: WebSocket, username: str):
    """
    Substitui ChatConsumer — WebSocket para conversa entre 2 usuários.
    O front envia ?me=<usuario_logado> na URL para identificar o remetente.
    """
    me = websocket.query_params.get("me")
    if not me:
        await websocket.close()
        return

    # Nome único de sala (igual ao Channels)
    room = f"chat_{'_'.join(sorted([me, username]))}"

    await manager.connect(websocket, room)
    print(f"🟢 {me} conectado à sala {room}")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            msg = {
                "type": "chat_message",
                "message": payload.get("message"),
                "username": me,
                "timestamp": payload.get("timestamp"),
                "image_url": payload.get("image_url"),
            }
            # Envia aos sockets locais e publica no Redis (para outras instâncias)
            await manager.broadcast_local(room, msg)
            await manager.redis.publish(room, json.dumps(msg))
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        print(f"🔴 {me} saiu da sala {room}")
    except Exception as e:
        print(f"⚠️ Erro no WebSocket de {me}: {e}")
        await websocket.close()


# === NOTIFICAÇÕES SOCKET ===
@app.websocket("/ws/notifications/")
async def notification_socket(websocket: WebSocket):
    """
    Substitui NotificationConsumer — notifica mensagens novas.
    O front deve enviar ?user=<id_usuario> na URL.
    """
    user_id = websocket.query_params.get("user")
    if not user_id:
        await websocket.close()
        return

    room = f"notifications_user_{user_id}"
    await manager.connect(websocket, room)
    print(f"🔔 Notificações ativas para user {user_id}")

    try:
        while True:
            await asyncio.sleep(60)  # Mantém a conexão viva
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        print(f"🔕 Notificações encerradas user {user_id}")
