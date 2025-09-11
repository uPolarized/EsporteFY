from django.shortcuts import render
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views.generic import TemplateView

class LoginView(DjangoLoginView):
    template_name = "account/login.html"

# ADICIONE ESTA NOVA VIEW
class HomeView(TemplateView):
    template_name = "home.html" # Vamos criar este arquivo a seguir
