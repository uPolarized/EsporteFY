from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Rota da página (GET)
    path('chat/conversa/<str:username>/', views.ConversaView.as_view(), name='conversa'),
    
    # Rota de envio AJAX (POST) - Essencial para o funcionamento!
    path('chat/enviar/<str:username>/', views.enviar_mensagem, name='enviar_mensagem'),
]