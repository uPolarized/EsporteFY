from django import forms
from .models import Perfil

# --- Formulário para Cadastro (com os campos extras) ---
class CustomSignupForm(forms.Form):
    username = forms.CharField(max_length=30, label='Nome de Usuário')
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

    def signup(self, request, user):
        user.username = self.cleaned_data['username']
        perfil = user.perfil
        perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        perfil.nivel_habilidade = self.cleaned_data['nivel_habilidade']
        perfil.idade = self.cleaned_data.get('idade')
        
        user.save()
        perfil.save()

# --- Formulário para Editar o Perfil (estava faltando) ---
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'bio', 'esportes_preferidos', 'nivel_habilidade', 'idade']