from django.urls import path
from . import views
from perfis.views import CustomPasswordSetView

app_name = 'perfis'

urlpatterns = [
    path('meu/', views.MeuPerfilView.as_view(), name='meu_perfil'),
    path('usuario/<str:username>/', views.VerPerfilView.as_view(), name='ver_perfil'),
    path('editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),
    path('usuarios/', views.ListaUsuariosView.as_view(), name='lista_usuarios'),

    # 🎯 Compatível com o JS atual:
    path('aceitar/<int:solicitacao_id>/', views.aceitar_solicitacao, name='aceitar_solicitacao_alt'),
    path('recusar/<int:solicitacao_id>/', views.recusar_solicitacao, name='recusar_solicitacao_alt'),

    # 🧩 E mantém as rotas “oficiais”
    path('solicitacao/enviar/<int:receptor_id>/', views.enviar_solicitacao_amizade, name='enviar_solicitacao'),
    path('solicitacao/aceitar/<int:solicitacao_id>/', views.aceitar_solicitacao, name='aceitar_solicitacao'),
    path('solicitacao/recusar/<int:solicitacao_id>/', views.recusar_solicitacao, name='recusar_solicitacao'),

    path('remover-amigo/<int:user_id>/', views.remover_amigo, name='remover_amigo'),
    path('accounts/password/set/', CustomPasswordSetView.as_view(), name='account_set_password'),
]
