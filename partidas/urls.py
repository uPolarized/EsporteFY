from django.urls import path
from . import views

app_name = 'partidas'

urlpatterns = [
    # Criar partida
    path('criar/', views.CriarPartidaView.as_view(), name='criar_partida'),

    # Participar / sair / cancelar
    path('<int:partida_id>/participar/', views.participar_partida, name='participar_partida'),
    path('<int:partida_id>/interesse/', views.registrar_interesse_partida, name='registrar_interesse_partida'),
    path('<int:partida_id>/confirmar/', views.confirmar_presenca_partida, name='confirmar_presenca_partida'),
    path('<int:partida_id>/recusar/', views.recusar_partida, name='recusar_partida'),
    path('<int:partida_id>/jogador/<int:jogador_id>/aprovar/', views.aprovar_jogador_partida, name='aprovar_jogador_partida'),
    path('<int:partida_id>/jogador/<int:jogador_id>/recusar/', views.recusar_jogador_partida, name='recusar_jogador_partida'),
    path('<int:partida_id>/sair/', views.sair_da_partida, name='sair_da_partida'),
    path('<int:partida_id>/cancelar/', views.cancelar_partida, name='cancelar_partida'),

    # Minhas partidas
    path('minhas/', views.MinhasPartidasView.as_view(), name='minhas_partidas'),

    # Avaliar partida
    path('statuses/', views.partidas_statuses, name='partidas_statuses'),

    path('<int:partida_id>/avaliar/', views.avaliar_partida, name='avaliar_partida'),
    path('api/esportes/', views.api_esportes, name='api_esportes'),
]

