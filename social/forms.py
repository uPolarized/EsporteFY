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

    def clean_conteudo(self):
        conteudo = (self.cleaned_data.get('conteudo') or '').strip()
        if len(conteudo) > 5000:
            raise forms.ValidationError('Mensagem muito longa (máximo de 5000 caracteres).')
        return conteudo

    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')
        if imagem and imagem.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Imagem muito grande (máximo de 10MB).')
        return imagem
