from django import forms
from .models import Perfil

# Definimos a opção vazia uma vez para reutilizá-la
EMPTY_CHOICE = [('', 'Selecione uma opção')]

class CustomSignupForm(forms.Form):
    username = forms.CharField(max_length=30, label='Nome de Usuário')
    
    # Adicionamos a opção vazia antes das opções do modelo
    esporte_preferido = forms.ChoiceField(
        choices=EMPTY_CHOICE + Perfil.ESPORTES_CHOICES,
        label="Qual seu esporte principal?",
        required=False
    )
    
    # Fazemos o mesmo para o nível de habilidade
    nivel_habilidade = forms.ChoiceField(
        choices=EMPTY_CHOICE + Perfil.NIVEL_HABILIDADE_CHOICES,
        label="Qual seu nível de habilidade?",
        required=False
    )
    
    idade = forms.IntegerField(label="Idade", required=False)

    def signup(self, request, user):
        user.username = self.cleaned_data['username']
        perfil = user.perfil
        perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        perfil.nivel_habilidade = self.cleaned_data['nivel_habilidade']
        perfil.idade = self.cleaned_data.get('idade')
        
        user.save()
        perfil.save()
