from django import forms
from django.utils import timezone
from .models import Partida, AvaliacaoQuadra, AvaliacaoJogador
from quadras.models import Quadra

class PartidaForm(forms.ModelForm):
    
    # --- MUDANÇA PRINCIPAL AQUI ---
    # Nós ainda definimos o campo, mas dizemos ao Django para 
    # usar um widget "escondido" (HiddenInput).
    # O mapa cuidará de preencher o valor deste campo.
    quadra = forms.ModelChoiceField(
        queryset=Quadra.objects.all(),
        widget=forms.HiddenInput(),  # <-- ESTA É A CORREÇÃO!
        required=True
    )
    
    class Meta:
        model = Partida
        fields = [
            'titulo',
            'esporte',
            'quadra',
            'data_hora',
            'jogadores_necessarios',
        ]
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    # Sua validação de data está perfeita, mantenha ela
    def clean_data_hora(self):
        data_partida = self.cleaned_data.get('data_hora')
        if data_partida and data_partida < timezone.now():
            raise forms.ValidationError("Não pode criar uma partida numa data que já passou.")
        return data_partida

# --- O resto dos formulários de avaliação continua igual ---

class AvaliacaoQuadraForm(forms.ModelForm):
    nota_quadra = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="A sua nota para a quadra"
    )
    class Meta:
        model = AvaliacaoQuadra
        fields = ['nota_quadra', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Deixe um comentário sobre a quadra (opcional)...'}),
        }

class AvaliacaoJogadorForm(forms.ModelForm):
    nota_fair_play = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Nota de Fair Play"
    )
    class Meta:
        model = AvaliacaoJogador
        fields = ['nota_fair_play']