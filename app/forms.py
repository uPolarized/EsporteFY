from django import forms
from allauth.account.forms import SignupForm, SetPasswordForm, ChangePasswordForm
from perfis.models import Perfil
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from .models import DataAccessRequest, Feedback


# ============================
# SIGNUP FORM (CADASTRO)
# ============================
class CustomSignupForm(SignupForm):
    username = forms.CharField(
        max_length=30,
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={'placeholder': 'Escolha um nome de usuário'})
    )

    esporte_preferido = forms.ChoiceField(
        choices=Perfil.ESPORTES_CHOICES,
        label="Qual seu esporte principal?",
        required=False
    )

    # Aqui está o CAPTCHA correto para V2
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'username',
            'email',
            'esporte_preferido',
            'password',
            'password2',
            'captcha',
        )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.username = self.cleaned_data['username']
        user.perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        user.save()
        user.perfil.save()
        return user


# ============================
# SET NEW PASSWORD (quando logado)
# ============================
class CustomPasswordSetForm(SetPasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )


# ============================
# CHANGE PASSWORD (trocar senha)
# ============================
class CustomChangePasswordForm(ChangePasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )


class DataAccessRequestForm(forms.ModelForm):
    class Meta:
        model = DataAccessRequest
        fields = ["motivo"]
        widgets = {
            "motivo": forms.Textarea(
                attrs={
                    "class": "lgpd-textarea",
                    "rows": 3,
                    "placeholder": "Descreva o motivo da solicitacao (opcional).",
                }
            )
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["categoria", "assunto", "mensagem", "email_contato"]
        widgets = {
            "categoria": forms.RadioSelect,
            "assunto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Resumo do seu feedback",
                    "maxlength": 200,
                }
            ),
            "mensagem": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Descreva com detalhes para podermos te ajudar melhor.",
                }
            ),
            "email_contato": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "seu@email.com",
                }
            ),
        }