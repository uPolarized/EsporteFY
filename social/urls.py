from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('chat/', views.CaixaDeEntradaView.as_view(), name='caixa_de_entrada'),
    path('chat/conversa/<str:username>/', views.ConversaView.as_view(), name='conversa'),
    
]