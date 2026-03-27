from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Rota da página (GET)
    path('chat/conversa/<str:username>/', views.ConversaView.as_view(), name='conversa'),
    
    # Rota de envio AJAX (POST) - Essencial para o funcionamento!
    path('chat/enviar/<str:username>/', views.enviar_mensagem, name='enviar_mensagem'),
    
    # Rota de like em atividades (POST)
    path('atividade/<int:atividade_id>/like/', views.toggle_like_atividade, name='toggle_like_atividade'),
]