from django.urls import path
from . import views

# Este app_name é opcional mas recomendado para organização
app_name = 'quadras'

urlpatterns = [
    # Esta é a view que o nosso mapa vai chamar
    # A URL completa será /api/quadras/ (definida no urls.py principal)
    path('', views.api_lista_quadras, name='api_lista_quadras'),
]