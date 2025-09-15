from django import forms
from .models import Partida

class PartidaForm(forms.ModelForm):
    class Meta:
        model = Partida
        # Lista dos campos do modelo que o usuário poderá preencher
        fields = [
            'titulo',
            'esporte',
            'bairro',
            'local',
            'data_hora',
            'jogadores_necessarios',
        ]
        # Adiciona um widget para facilitar a seleção de data e hora
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }