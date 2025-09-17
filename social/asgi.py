import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import social.routing  # suas rotas de websocket

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
django.setup()  # garante que o Django está carregado antes de usar Channels

# --- Debug para garantir que o arquivo é carregado ---
print(">>> ASGI file loaded")

application = ProtocolTypeRouter({
    # HTTP normal pelo Django
    "http": django.core.asgi.get_asgi_application(),
    
    # WebSocket pelo Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            social.routing.websocket_urlpatterns
        )
    ),
})
