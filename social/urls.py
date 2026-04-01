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

    # Feed social (posts e comentários)
    path('posts/', views.listar_posts, name='listar_posts'),
    path('posts/criar/', views.criar_post, name='criar_post'),
    path('post/<int:post_id>/like/', views.toggle_like_post, name='toggle_like_post'),
    path('post/<int:post_id>/comentar/', views.comentar_post, name='comentar_post'),
    path('post/<int:post_id>/deletar/', views.deletar_post, name='deletar_post'),
    path('post/<int:post_id>/visibilidade/', views.atualizar_visibilidade_post, name='atualizar_visibilidade_post'),
    path('post/<int:post_id>/fixar/', views.toggle_fixar_post, name='toggle_fixar_post'),
    path('comentario/<int:comentario_id>/like/', views.toggle_like_comentario, name='toggle_like_comentario'),
    path('comentario/<int:comentario_id>/deletar/', views.deletar_comentario, name='deletar_comentario'),
    path('comentario/<int:comentario_id>/fixar/', views.toggle_fixar_comentario, name='toggle_fixar_comentario'),
]