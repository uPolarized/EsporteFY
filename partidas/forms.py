from django import forms
from django.utils import timezone
from .models import Partida, AvaliacaoQuadra, AvaliacaoJogador
from quadras.models import Quadra
from .models import Esporte  # ✅ agora importa do mesmo app



class PartidaForm(forms.ModelForm):
    # Campo de quadra — controlado pelo mapa, permanece oculto
    quadra = forms.ModelChoiceField(
        queryset=Quadra.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )

    # Campo de esporte — agora é dinâmico (dropdown com esportes do banco)
    esporte = forms.ModelChoiceField(
        queryset=Esporte.objects.all(),
        label="Esporte",
        empty_label="Selecione um esporte",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Partida
        fields = [
            "titulo",
            "esporte",
            "quadra",
            "data_hora",
            "jogadores_necessarios",
        ]
        widgets = {
            "data_hora": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_data_hora(self):
        """Impede criação de partidas em datas passadas."""
        data_partida = self.cleaned_data.get("data_hora")
        if data_partida and data_partida < timezone.now():
            raise forms.ValidationError("Não pode criar uma partida numa data que já passou.")
        return data_partida


# --- Formulário de avaliação da quadra ---
class AvaliacaoQuadraForm(forms.ModelForm):
    nota_quadra = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="A sua nota para a quadra"
    )

    class Meta:
        model = AvaliacaoQuadra
        fields = ["nota_quadra", "comentario"]
        widgets = {
            "comentario": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Deixe um comentário sobre a quadra (opcional)..."
            }),
        }


# --- Formulário de avaliação do jogador ---
class AvaliacaoJogadorForm(forms.ModelForm):
    nota_fair_play = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Nota de Fair Play"
    )

    class Meta:
        model = AvaliacaoJogador
        fields = ["nota_fair_play"]
