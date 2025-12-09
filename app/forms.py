from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Prefetch
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache # ✅ OTIMIZAÇÃO: Importa o cache do Django
from django.contrib.contenttypes.models import ContentType # ✅ OTIMIZAÇÃO: Para pré-buscar GFKs

# Importações dos modelos e API
import requests
from partidas.models import Partida
from quadras.models import Quadra
from social.models import Atividade
# ✅ OTIMIZAÇÃO: As funções da API são importadas do cliente,
# não definidas localmente.
from conteudo.api_client import buscar_noticias_esportivas, buscar_clima_marica, buscar_previsao_chuva


class HomeView(View):
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('feed')
        return render(request, self.template_name)

class FeedView(LoginRequiredMixin, View):
    
    template_name = 'feed.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request=request)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = {}
        request = kwargs.get('request') # Pega o request para o filtro de bairro

        # --- 1. OTIMIZAÇÃO DE API (Cache) ---
        # Tenta buscar os dados do cache. Se não existirem,
        # chama a API e armazena os dados no cache.

        # Cache do Clima (10 minutos)
        context['clima_atual'] = cache.get('clima_marica')
        if not context['clima_atual']:
            clima_data = buscar_clima_marica()
            if clima_data:
                cache.set('clima_marica', clima_data, 600) # 600s = 10 min
                context['clima_atual'] = clima_data

        # Cache das Notícias (30 minutos)
        context['noticias'] = cache.get('noticias_esportivas')
        if not context['noticias']:
            noticias_data = buscar_noticias_esportivas()
            if noticias_data:
                cache.set('noticias_esportivas', noticias_data, 1800) # 1800s = 30 min
                context['noticias'] = noticias_data

        # Cache da Previsão (10 minutos)
        context['previsao_chuva'] = cache.get('previsao_chuva_marica')
        if not context['previsao_chuva']:
            previsao_data = buscar_previsao_chuva()
            if previsao_data:
                cache.set('previsao_chuva_marica', previsao_data, 600)
                context['previsao_chuva'] = previsao_data
        

        # --- 2. OTIMIZAÇÃO DE PARTIDAS (N+1) ---
        
        bairro_filtrado = request.GET.get('bairro', 'todos')
        
        # ✅ OTIMIZAÇÃO: Adicionado prefetch_related('jogadores_confirmados')
        # Isso busca todos os jogadores de todas as partidas em UMA consulta.
        partidas_list = Partida.objects.filter(
            data_hora__gte=timezone.now()
        ).select_related(
            'quadra'
        ).prefetch_related(
            'jogadores_confirmados' # <- A mágica acontece aqui
        ).order_by('data_hora') # Boa prática adicionar um order_by

        if bairro_filtrado and bairro_filtrado != 'todos':
            partidas_list = partidas_list.filter(quadra__bairro=bairro_filtrado)
        
        context['partidas'] = partidas_list
        context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
        context['bairro_atual'] = bairro_filtrado
        context['bairro_atual_nome'] = dict(Quadra.BAIRRO_CHOICES).get(bairro_filtrado, 'Todos')

        
        # --- 3. OTIMIZAÇÃO DE ATIVIDADES (N+1 com GFK) ---
        
        uma_semana_atras = timezone.now() - timedelta(days=7)

        # ✅ OTIMIZAÇÃO: select_related('ator__perfil') já estava ótimo.
        atividades_list = Atividade.objects.filter(
            timestamp__gte=uma_semana_atras
        ).select_related(
            'ator__perfil'
        ).order_by('-timestamp')[:20] # Limita a 20 atividades

        # ✅ OTIMIZAÇÃO: Pré-busca manual dos GenericForeignKeys (GFK)
        # 1. Agrupa IDs de objeto por tipo de conteúdo (ex: Partida, User)
        gfk_map = {}
        for atividade in atividades_list:
            if atividade.content_type_id not in gfk_map:
                gfk_map[atividade.content_type_id] = []
            gfk_map[atividade.content_type_id].append(atividade.object_id)

        # 2. Busca os objetos em si (ex: todas as Partidas) de uma vez
        content_cache = {}
        for ct_id, object_ids in gfk_map.items():
            try:
                ct = ContentType.objects.get_for_id(ct_id)
                model_class = ct.model_class()
                
                # Otimização específica: Se for Partida, busca a quadra junto
                if model_class == Partida:
                    queryset = model_class.objects.filter(id__in=object_ids).select_related('quadra')
                else:
                    queryset = model_class.objects.filter(id__in=object_ids)
                
                # Adiciona ao cache
                for obj in queryset:
                    content_cache[(ct_id, obj.id)] = obj
                    
            except Exception as e:
                print(f"Erro ao pré-buscar GFK: {e}") # Log de erro

        
        for atividade in atividades_list:
            atividade.alvo = content_cache.get((atividade.content_type_id, atividade.object_id))

        context['atividades'] = atividades_list
        
        return context





from django import forms
from allauth.account.forms import SignupForm, SetPasswordForm, ChangePasswordForm
from perfis.models import Perfil
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


# ============================
# SIGNUP FORM (CADASTRO)
# ============================
class CustomSignupForm(SignupForm):
    username = forms.CharField(
        max_length=30,
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={'placeholder': 'Escolha um nome de usuário'})
    )

    esporte_preferido = forms.ChoiceField(
        choices=Perfil.ESPORTES_CHOICES,
        label="Qual seu esporte principal?",
        required=False
    )

    # Aqui está o CAPTCHA correto para V2
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'username',
            'email',
            'esporte_preferido',
            'password',
            'password2',
            'captcha',
        )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.username = self.cleaned_data['username']
        user.perfil.esportes_preferidos = self.cleaned_data['esporte_preferido']
        user.save()
        user.perfil.save()
        return user


# ============================
# SET NEW PASSWORD (quando logado)
# ============================
class CustomPasswordSetForm(SetPasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )


# ============================
# CHANGE PASSWORD (trocar senha)
# ============================
class CustomChangePasswordForm(ChangePasswordForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'dark',
            'data-size': 'normal',
        })
    )