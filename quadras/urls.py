from django.urls import path
from .views import QuadraListAPIView

app_name = 'quadras'

urlpatterns = [
    path('', QuadraListAPIView.as_view(), name='api_lista_quadras'),
]
