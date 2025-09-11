from django.urls import path
from django.views.generic import TemplateView
from .views import LoginView, HomeView # Importe a HomeView
from .views import CustomSignupView

urlpatterns = [
    # Esta linha define a página inicial
    path('', HomeView.as_view(), name='home'),
    path("signup/", CustomSignupView.as_view(), name="account_signup"),
    path('login/', LoginView.as_view(), name='login'),
]