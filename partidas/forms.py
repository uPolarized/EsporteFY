from django import forms
from .models import Partida, AvaliacaoQuadra, AvaliacaoJogador # Corrigido aqui
from django.utils import timezone  

class PartidaForm(forms.ModelForm):
    class Meta:
        model = Partida
        fields = [
            'titulo',
            'esporte',
            'bairro',
            'local',
            'data_hora',
            'jogadores_necessarios',
        ]
        widgets = {
            'data_hora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class AvaliacaoQuadraForm(forms.ModelForm):
    nota_quadra = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Sua nota para a quadra"
    )
    class Meta:
        model = AvaliacaoQuadra # Corrigido aqui
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


      # --- LÓGICA DE VALIDAÇÃO ADICIONADA AQUI ---
    def clean_data_hora(self):
        # 2. Pega o valor do campo de data e hora que o usuário enviou
        data_partida = self.cleaned_data.get('data_hora')

        # 3. Verifica se a data e hora não é nula e se é anterior ao momento atual
        if data_partida and data_partida < timezone.now():
            # 4. Se for no passado, lança um erro de validação
            raise forms.ValidationError("Você não pode criar uma partida em uma data ou hora que já passou.")
        
        # 5. Se a data for válida (no futuro), retorna o valor para continuar o processo
        return data_partida