from django import forms
from .models import Perfil
from quadras.models import Quadra
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from allauth.account.forms import SetPasswordForm, ChangePasswordForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from allauth.account.forms import ResetPasswordForm


# ============================================================
# FORMULÁRIO DE EDITAR PERFIL
# ============================================================
class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [
            'foto',
            'banner',
            'banner_position',
            'mini_bio',
            'esportes_preferidos',
            'nivel_habilidade',
            'bairro_base',
            'idade',
            'cidade',
        ]
        labels = {
            'mini_bio': 'Sobre Mim',
            'esportes_preferidos': 'Esportes Preferidos',
            'nivel_habilidade': 'Nível de Habilidade',
            'bairro_base': 'Bairro Principal',
            'idade': 'Idade',
            'cidade': 'Cidade',
            'banner': 'Banner do Perfil',
            'banner_position': 'Posição do Banner',
        }
        widgets = {
            # O valor de banner_position vem do JavaScript (drag to reposition)
            'banner_position': forms.HiddenInput(),
        }

    # ── Validação da FOTO DE PERFIL ──────────────────────────
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            if hasattr(field, 'choices'):
                from django.utils.translation import gettext_lazy as _
                new_choices = []
                for val, label in field.choices:
                    if val == '' or label == '---------':
                        new_choices.append((val, "Nenhum"))
                    else:
                        new_choices.append((val, label))
                field.choices = new_choices

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            if hasattr(field, 'choices'):
                from django.utils.translation import gettext_lazy as _
                new_choices = []
                for val, label in field.choices:
                    if val == '' or label == '---------':
                        new_choices.append((val, "Nenhum"))
                    else:
                        new_choices.append((val, label))
                field.choices = new_choices

    def clean_foto(self):
        from PIL import Image

        foto = self.cleaned_data.get('foto')
        if not foto or not hasattr(foto, 'file'):
            return foto

        if foto.size > 25 * 1024 * 1024:
            raise forms.ValidationError("Imagem muito grande. Tamanho máximo: 25 MB.")

        try:
            foto.seek(0)
            img = Image.open(foto)
            img.load()
            fmt = img.format
        except Exception:
            raise forms.ValidationError(
                "Arquivo inválido ou corrompido. Envie uma imagem JPG, PNG, WEBP ou GIF."
            )
        finally:
            foto.seek(0)

        allowed_formats = {'JPEG', 'PNG', 'WEBP', 'GIF'}
        if fmt not in allowed_formats:
            raise forms.ValidationError(
                f"Formato não permitido ({fmt}). Use JPG, PNG, WEBP ou GIF."
            )

        return foto

    # ── Validação do BANNER ──────────────────────────────────
    def clean_banner(self):
        from PIL import Image

        banner = self.cleaned_data.get('banner')
        if not banner or not hasattr(banner, 'file'):
            return banner

        if banner.size > 50 * 1024 * 1024:  # era 10MB, agora 50MB
            raise forms.ValidationError("Banner muito grande. Tamanho máximo: 50 MB.")

        try:
            banner.seek(0)
            img = Image.open(banner)
            img.load()
            fmt = img.format
        except Exception:
            raise forms.ValidationError(
                "Arquivo inválido ou corrompido. Envie JPG, PNG, WEBP ou GIF."
            )
        finally:
            banner.seek(0)

        allowed_formats = {'JPEG', 'PNG', 'WEBP', 'GIF'}
        if fmt not in allowed_formats:
            raise forms.ValidationError(
                f"Formato não permitido ({fmt}). Use JPG, PNG, WEBP ou GIF."
            )

        return banner


# ============================================================
# FORMULÁRIO DE FILTRO DE USUÁRIOS
# ============================================================
class FiltroUsuarioForm(forms.Form):
    nome_usuario = forms.CharField(
        label='Buscar por nome',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Digite um nome de usuário...', 'class': 'form-control'})
    )
    esporte = forms.ChoiceField(
        label='Filtrar por Esportes',
        required=False,
        choices=[('', 'Todos')] + Perfil.ESPORTES_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    nivel = forms.ChoiceField(
        label='Filtrar por Nível',
        required=False,
        choices=[('', 'Todos')] + Perfil.NIVEL_HABILIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    bairro = forms.ChoiceField(
        label='Filtrar por Bairro',
        required=False,
        choices=[('', 'Todos')] + list(Quadra.BAIRRO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                classes = field.widget.attrs.get('class', '')
                if 'form-control' not in classes and 'form-select' not in classes:
                    field.widget.attrs['class'] = f"{classes} form-control".strip()


# ============================================================
# FORMULÁRIOS DE SENHA / CAPTCHA
# ============================================================
class CustomSetPasswordForm(SetPasswordForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())


class SetPasswordCaptchaForm(SetPasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'new_password1',
            'new_password2',
            'captcha'
        )


class ChangePasswordCaptchaForm(ChangePasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )


class CustomResetPasswordForm(ResetPasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            "data-theme": "dark",
            "data-size": "normal",
        })
    )