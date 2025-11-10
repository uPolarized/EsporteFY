from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("chat/conversa/<str:username>/", views.ConversaView.as_view(), name="conversa"),
    path("chat/enviar/<str:username>/", views.enviar_mensagem, name="enviar_mensagem"),
]
