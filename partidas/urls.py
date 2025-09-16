from django.urls import path
from . import views

app_name = 'partidas'

urlpatterns = [
    path('criar/', views.CriarPartidaView.as_view(), name='criar_partida'),
    # --- NOVAS ROTAS AQUI ---
    path('<int:partida_id>/participar/', views.participar_partida, name='participar_partida'),
    path('<int:partida_id>/sair/', views.sair_da_partida, name='sair_da_partida'),
    path('minhas/', views.MinhasPartidasView.as_view(), name='minhas_partidas'),
    path('<int:partida_id>/avaliar/', views.avaliar_partida, name='avaliar_partida'),
]