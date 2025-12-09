import json
import asyncio
import os
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configurações
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="EsporteFY Chat Debug")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        await pubsub.psubscribe("chat_*", "notifications_*")
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
    if not me: await websocket.close(); return

    # --- LÓGICA DE NOME DA SALA ---
    # Tem que ser idêntica ao Django
    u1 = me.lower().strip()
    u2 = username.lower().strip()
    room = f"chat_{'_'.join(sorted([u1, u2]))}"
    
    print(f"🔍 [FastAPI] Cliente '{me}' conectando na sala: '{room}'")

    await manager.connect(websocket, room)
    try:
        while True: await websocket.receive_text()
    except:
        manager.disconnect(websocket, room)

@app.websocket("/ws/notifications/")
async def notification_socket(websocket: WebSocket):
    user_id = websocket.query_params.get("user")
    if not user_id: await websocket.close(); return
    
    room = f"notifications_user_{user_id}"
    print(f"🔔 [FastAPI] Notificações para sala: '{room}'")
    
    await manager.connect(websocket, room)
    try:
        while True: await websocket.receive_text()
    except:
        manager.disconnect(websocket, room)