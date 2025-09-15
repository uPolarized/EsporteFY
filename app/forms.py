from django import forms
from allauth.account.forms import SignupForm
from perfis.models import Perfil
# Imports do Crispy Forms
# from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class CustomSignupForm(SignupForm):
    # Nossos campos customizados continuam aqui
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

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Cria um helper para controlar o layout
        self.helper = FormHelper()
        self.helper.form_tag = False # Diz ao Crispy para não renderizar a tag <form>
        self.helper.layout = Layout(
            # Define a ordem exata dos campos que queremos exibir
            'username',
            'email',
            'esporte_preferido',
            'password',
            'password2',
        )

    # O método save continua o mesmo
    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.username = self.cleaned_data['username']
        user.perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        user.save()
        user.perfil.save()
        return user