from django import forms
from .models import Perfil

# Importação agora é SEGURA, pois o CustomSignupForm não está mais aqui
from allauth.account.forms import SetPasswordForm
from django_recaptcha.fields import ReCaptchaField  # <--- CORRIGIDO
from django_recaptcha.widgets import ReCaptchaV2Checkbox  # <--- CORRIGIDO

# --- Formulário para Cadastro FOI MOVIDO PARA 'perfis/signup_form.py' ---


# --- Formulário para Editar o Perfil ---
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [
            'foto',
            'mini_bio',
            'esportes_preferidos',
            'nivel_habilidade',
            'idade',
            'cidade',
        ]
        labels = {
            'mini_bio': 'Sobre Mim',
            'esportes_preferidos': 'Esportes Preferidos',
            'nivel_habilidade': 'Nível de Habilidade',
            'idade': 'Idade',
            'cidade': 'Cidade',
        }

class FiltroUsuarioForm(forms.Form):
    # Campo de busca por nome, não obrigatório
    nome_usuario = forms.CharField(
        label='Buscar por nome',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Digite um nome de usuário...'})
    )

    # Campo de filtro por desporto, não obrigatório
    esporte = forms.ChoiceField(
        label='Filtrar por Esportes',
        required=False,
        choices=[('', 'Todos os Esportes')] + Perfil.ESPORTES_CHOICES
    )

    # Campo de filtro por nível, não obrigatório
    nivel = forms.ChoiceField(
        label='Filtrar por Nível',
        required=False,
        choices=[('', 'Todos os Níveis')] + Perfil.NIVEL_HABILIDADE_CHOICES
    )

class SetPasswordCaptchaForm(SetPasswordForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())