from django.urls import path
from . import views

app_name = 'partidas'

urlpatterns = [
    # Criar partida
    path('criar/', views.CriarPartidaView.as_view(), name='criar_partida'),

    # Participar / sair / cancelar
    path('<int:partida_id>/participar/', views.participar_partida, name='participar_partida'),
    path('<int:partida_id>/sair/', views.sair_da_partida, name='sair_da_partida'),
    path('<int:partida_id>/cancelar/', views.cancelar_partida, name='cancelar_partida'),

    # Minhas partidas
    path('minhas/', views.MinhasPartidasView.as_view(), name='minhas_partidas'),

    # Avaliar partida
    path('statuses/', views.partidas_statuses, name='partidas_statuses'),

    path('<int:partida_id>/avaliar/', views.avaliar_partida, name='avaliar_partida'),
    path('api/esportes/', views.api_esportes, name='api_esportes'),
]

