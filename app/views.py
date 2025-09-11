from django.shortcuts import render
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views.generic import TemplateView
from allauth.account.views import SignupView
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

class LoginView(DjangoLoginView):
    template_name = "account/login.html"

# ADICIONE ESTA NOVA VIEW
class HomeView(TemplateView):
    template_name = "home.html" # Vamos criar este arquivo a seguir


@method_decorator(sensitive_post_parameters(), name='dispatch')
class CustomSignupView(SignupView):
    template_name = "account/signup.html"

    # Sobrescrevendo a função de redirecionamento
    def dispatch(self, request, *args, **kwargs):
        # Permite acessar mesmo se estiver logado
        return super().dispatch(request, *args, **kwargs)