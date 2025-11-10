from django import forms
from .models import Mensagem

class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['conteudo', 'imagem']
        widgets = {
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Digite sua mensagem...',
                'style': 'resize:none; background:#1e1e1e; color:#f1f1f1; border:1px solid #444;'
            }),
        }
