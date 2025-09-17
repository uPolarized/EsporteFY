from django import forms

class MensagemForm(forms.Form):
    conteudo = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Digite sua mensagem..."
        })
    )