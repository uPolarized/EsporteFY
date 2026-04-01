from django import forms
from django.db import connection

from app.models import DocumentoLGPD, UserConsentLog
from perfis.models import Perfil
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


def _table_exists(table_name):
    try:
        return table_name in connection.introspection.table_names()
    except Exception:
        return False


def _get_latest_document_version(doc_type):
    if not _table_exists(DocumentoLGPD._meta.db_table):
        return "1.0"
    doc = (
        DocumentoLGPD.objects.filter(tipo_documento=doc_type, ativo=True)
        .order_by("-data_vigencia", "-atualizado_em")
        .first()
    )
    if doc and doc.versao:
        return doc.versao
    return "1.0"


def _get_client_ip(request):
    if not request:
        return ""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")

class CustomSignupForm(forms.Form):
    username = forms.CharField(max_length=30, label='Nome de Usuário')
    
    # --- AQUI ESTÁ A MUDANÇA ---
    email = forms.EmailField(
        label="E-mail", 
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'exemplo@email.com'}),
        error_messages={
            'required': 'Por favor, preencha este campo.',
            'invalid': 'Insira um email válido.',  # <--- É essa mensagem que aparecerá se o formato estiver errado
        }
    )
    # ---------------------------

    esporte_preferido = forms.ChoiceField(
        choices=([('', 'Nenhum Selecionado')] + Perfil.ESPORTES_CHOICES),
        label="Qual seu esporte principal?",
        required=False
    )

    nivel_habilidade = forms.ChoiceField(
        choices=([('', 'Nenhum Selecionado')] + Perfil.NIVEL_HABILIDADE_CHOICES),
        label="nível de habilidade?",
        required=False
    )


    idade = forms.IntegerField(label='Idade', required=False)

    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )

    aceita_termos = forms.BooleanField(
        required=True,
        label='Li e aceito os Termos de Servico',
        error_messages={'required': 'Voce precisa aceitar os Termos de Servico.'},
    )

    aceita_politica = forms.BooleanField(
        required=True,
        label='Li e aceito a Politica de Privacidade',
        error_messages={'required': 'Voce precisa aceitar a Politica de Privacidade.'},
    )

    aceita_cookies = forms.BooleanField(
        required=False,
        label='Aceito cookies opcionais para melhorar minha experiencia',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'username',
            'email',
            'esporte_preferido',
            'nivel_habilidade',
                        'idade',
            'captcha',
            'aceita_termos',
            'aceita_politica',
            'aceita_cookies',
        )

    def signup(self, request, user):
        if hasattr(user, 'perfil'):
            perfil = user.perfil
            perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
            perfil.nivel_habilidade = self.cleaned_data['nivel_habilidade']
            
            perfil.idade = self.cleaned_data.get('idade')
            perfil.save()
        else:
            Perfil.objects.create(
                user=user,
                esportes_preferidos=self.cleaned_data['esporte_preferido'],
                nivel_habilidade=self.cleaned_data['nivel_habilidade'],
                
                idade=self.cleaned_data.get('idade')
            )

        if _table_exists(UserConsentLog._meta.db_table):
            ip_address = _get_client_ip(request)
            user_agent = ''
            if request:
                user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:255]

            UserConsentLog.objects.create(
                user=user,
                consent_type=UserConsentLog.TYPE_TERMS,
                accepted=True,
                document_version=_get_latest_document_version('terms_of_service'),
                source='signup',
                ip_address=ip_address,
                user_agent=user_agent,
            )

            UserConsentLog.objects.create(
                user=user,
                consent_type=UserConsentLog.TYPE_PRIVACY,
                accepted=True,
                document_version=_get_latest_document_version('privacy_policy'),
                source='signup',
                ip_address=ip_address,
                user_agent=user_agent,
            )

            UserConsentLog.objects.create(
                user=user,
                consent_type=UserConsentLog.TYPE_COOKIES,
                accepted=bool(self.cleaned_data.get('aceita_cookies')),
                document_version='n/a',
                source='signup',
                ip_address=ip_address,
                user_agent=user_agent,
            )

        if request:
            request.session['force_lgpd_redirect'] = True

        return user