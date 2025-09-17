from django.urls import path
from . import views


app_name = 'perfis'

urlpatterns = [
    # URLs de perfil individual
    path('meu/', views.MeuPerfilView.as_view(), name='meu_perfil'),
    
     # Ex: /perfil/meu/ -> Mostra o perfil do próprio utilizador
    path('meu/', views.MeuPerfilView.as_view(), name='meu_perfil'),
    
    # Ex: /perfil/usuario/joao_victor/ -> Mostra o perfil público do joao_victor
    path('usuario/<str:username>/', views.VerPerfilView.as_view(), name='ver_perfil'),
    path('editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),
    
    # 2. Adiciona a rota que estava faltando para a lista de usuários
    path('usuarios/', views.ListaUsuariosView.as_view(), name='lista_usuarios'),
    
    # URLs para gerenciar solicitações de amizade
    path('solicitacao/enviar/<int:receptor_id>/', views.enviar_solicitacao_amizade, name='enviar_solicitacao'),
     # Rotas para as AÇÕES de aceitar ou recusar uma solicitação
    path('solicitacao/aceitar/<int:solicitacao_id>/', views.aceitar_solicitacao, name='aceitar_solicitacao'),
    path('solicitacao/recusar/<int:solicitacao_id>/', views.recusar_solicitacao, name='recusar_solicitacao'),

     path('remover-amigo/<int:user_id>/', views.remover_amigo, name='remover_amigo'),
]