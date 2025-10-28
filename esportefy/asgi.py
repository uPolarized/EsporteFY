import os
from django.core.asgi import get_asgi_application

# --- ETAPA 1: Carregar o Django e as settings ---
# Defina a variável de ambiente primeiro
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')

# Esta linha é crucial: ela carrega o Django e os apps
django_asgi_app = get_asgi_application()
# -----------------------------------------------


# --- ETAPA 2: Importar o Channels SÓ DEPOIS ---
# Agora que o Django está carregado, podemos importar o resto
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import social.routing  # Importa sua configuração de rotas

# -----------------------------------------------

application = ProtocolTypeRouter({
    # O 'http' usa a aplicação Django que já carregamos
    "http": django_asgi_app,

    # O 'websocket' usa o Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            social.routing.websocket_urlpatterns
        )
    ),
})