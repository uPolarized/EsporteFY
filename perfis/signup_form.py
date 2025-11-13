from django import forms
from allauth.account.utils import setup_user_email
from allauth.account.adapter import get_adapter
from perfis.models import Perfil
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class CustomSignupForm(forms.Form):
    username = forms.CharField(max_length=30, label='Nome de Usuário')
    email = forms.EmailField(label="E-mail", required=True)

    esporte_preferido = forms.ChoiceField(
        choices=Perfil.ESPORTES_CHOICES,
        label="Qual seu esporte principal?",
        required=False
    )

    nivel_habilidade = forms.ChoiceField(
        choices=Perfil.NIVEL_HABILIDADE_CHOICES,
        label="Qual seu nível de habilidade?",
        required=False
    )

    idade = forms.IntegerField(label="Idade", required=False)

    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'username',
            'email',
            'esporte_preferido',
            'nivel_habilidade',
            'idade',
            'captcha',
        )

    def signup(self, request, user):
        """Método oficial do Allauth para salvar dados adicionais."""
        adapter = get_adapter()
        adapter.clean_username(self.cleaned_data['username'])
        adapter.clean_email(self.cleaned_data['email'])

        # email
        user.email = self.cleaned_data['email']
        setup_user_email(request, user)

        # username
        user.username = self.cleaned_data['username']
        user.save()

        # perfil extra
        perfil = user.perfil
        perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        perfil.nivel_habilidade = self.cleaned_data['nivel_habilidade']
        perfil.idade = self.cleaned_data.get('idade')
        perfil.save()

        return user
