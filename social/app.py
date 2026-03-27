import json
import asyncio
import os
import time
import hmac
import hashlib
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configurações
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SECRET_KEY = os.getenv("SECRET_KEY", "")
WS_TOKEN_TTL_SECONDS = int(os.getenv("WS_TOKEN_TTL_SECONDS", "7200"))
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000").split(",")
    if origin.strip()
]

app = FastAPI(title="EsporteFY Chat Debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def is_valid_ws_token(user_id: str, username: str, token: str) -> bool:
    """Valida token assinado HMAC emitido pelo Django para WebSocket."""
    if not SECRET_KEY or not token or not user_id or not username:
        return False

    parts = token.split(":")
    if len(parts) != 4:
        return False

    token_user_id, token_username, token_ts, token_sig = parts

    if token_user_id != str(user_id) or token_username != str(username):
        return False

    try:
        ts = int(token_ts)
    except ValueError:
        return False

    if abs(int(time.time()) - ts) > WS_TOKEN_TTL_SECONDS:
        return False

    payload = f"{token_user_id}:{token_username}:{token_ts}"
    expected_sig = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, token_sig)

# Redis client global para status online
redis_client_global = None

async def get_redis_client():
    """Obter cliente Redis global"""
    global redis_client_global
    if redis_client_global is None:
        redis_client_global = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client_global

async def mark_user_online(user_identifier):
    """Marcar usuário como online (username ou user_id)"""
    try:
        client = await get_redis_client()
        # TTL de 1 hora - será atualizado a cada mensagem
        await client.setex(f"user_online:{user_identifier}", 3600, "1")
        print(f"✅ [Online] Usuário {user_identifier} marcado como ONLINE")
    except Exception as e:
        print(f"⚠️ Erro ao marcar usuário online: {e}")

async def mark_user_offline(user_identifier):
    """Marcar usuário como offline"""
    try:
        client = await get_redis_client()
        await client.delete(f"user_online:{user_identifier}")
        print(f"⚫ [Offline] Usuário {user_identifier} marcado como OFFLINE")
    except Exception as e:
        print(f"⚠️ Erro ao marcar usuário offline: {e}")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        print(f"🟢 [Manager] Socket ADICIONADO na sala: '{room}'")

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            if websocket in self.active_connections[room]:
                self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def broadcast_to_room(self, room: str, message: dict):
        if room in self.active_connections:
            print(f"📢 [Manager] ENVIANDO para sala '{room}' ({len(self.active_connections[room])} usuários)")
            for connection in list(self.active_connections[room]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"⚠️ Erro envio: {e}")
                    self.disconnect(connection, room)
        else:
            print(f"⚠️ [Manager] Sala '{room}' não encontrada ou vazia. Salas ativas: {list(self.active_connections.keys())}")

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

async def redis_listener():
    print(f"👂 [Redis] Conectando em {REDIS_URL}...")
    try:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.psubscribe("chat_*", "notifications_*", "feed_*")
        print("✅ [Redis] Escutando canais...")

        async for message in pubsub.listen():
            # Ignora mensagens de controle do Redis
            if message["type"] in ["subscribe", "psubscribe", "unsubscribe"]:
                continue
            
            # LOG CRÍTICO: Mostra TUDO que chega
            print(f"📨 [Redis RECEBEU] Canal: '{message['channel']}' | Dados: {message['data']}")

            if message["type"] == "pmessage":
                try:
                    room = message["channel"]
                    raw_data = message["data"]
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode('utf-8')
                    data = json.loads(raw_data)
                    
                    await manager.broadcast_to_room(room, data)
                except Exception as e:
                    print(f"❌ Erro processando msg: {e}")

    except Exception as e:
        print(f"🔥 ERRO CRÍTICO REDIS: {e}")

@app.websocket("/ws/chat/{username}/")
async def chat_socket(websocket: WebSocket, username: str):
    me = websocket.query_params.get("me")
    user_id = websocket.query_params.get("user")
    token = websocket.query_params.get("token")

    if not me or not user_id or not token or not is_valid_ws_token(user_id, me, token):
        await websocket.close(code=1008)
        return

    # --- LÓGICA DE NOME DA SALA ---
    # Tem que ser idêntica ao Django
    u1 = me.lower().strip()
    u2 = username.lower().strip()
    room = f"chat_{'_'.join(sorted([u1, u2]))}"

    print(f"🔍 [FastAPI] Cliente '{me}' conectando na sala: '{room}'")

    # Marcar usuário como online
    await mark_user_online(user_id)

    await manager.connect(websocket, room)
    try:
        while True:
            await websocket.receive_text()
    except:
        # Marcar como offline
        await mark_user_offline(user_id)
        manager.disconnect(websocket, room)

@app.websocket("/ws/notifications/")
async def notification_socket(websocket: WebSocket):
    user_id = websocket.query_params.get("user")
    username = websocket.query_params.get("username")
    token = websocket.query_params.get("token")

    if not user_id or not username or not token or not is_valid_ws_token(user_id, username, token):
        await websocket.close(code=1008)
        return

    room = f"notifications_user_{user_id}"
    print(f"🔔 [FastAPI] Notificações para sala: '{room}'")

    # Marcar usuário como online (usando user_id)
    await mark_user_online(user_id)

    await manager.connect(websocket, room)
    try:
        while True:
            await websocket.receive_text()
    except:
        # Marcar como offline
        await mark_user_offline(user_id)
        manager.disconnect(websocket, room)

@app.websocket("/ws/feed/")
async def feed_socket(websocket: WebSocket):
    user_id = websocket.query_params.get("user")
    username = websocket.query_params.get("username")
    token = websocket.query_params.get("token")

    if not user_id or not username or not token or not is_valid_ws_token(user_id, username, token):
        await websocket.close(code=1008)
        return

    room = "feed_all"
    print(f"📰 [FastAPI] Cliente conectado ao feed: '{room}'")

    await mark_user_online(user_id)

    await manager.connect(websocket, room)
    try:
        while True:
            await websocket.receive_text()
    except:
        await mark_user_offline(user_id)
        manager.disconnect(websocket, room)