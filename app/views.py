from django.shortcuts import render
from django.contrib.auth.views import LoginView as DjangoLoginView

class LoginView(DjangoLoginView):
    template_name = "authentication/login.html"

