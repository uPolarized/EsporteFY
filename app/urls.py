from django.urls import path
from django.views.generic import TemplateView
from .views import LoginView, HomeView # Importe a HomeView

urlpatterns = [
    # Esta linha define a página inicial
    path('', HomeView.as_view(), name='home'),

    path('login/', LoginView.as_view(), name='login'),
]