from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.db.models import Prefetch
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache # ✅ OTIMIZAÇÃO: Importa o cache do Django
from django.contrib.contenttypes.models import ContentType # ✅ OTIMIZAÇÃO: Para pré-buscar GFKs
from django.contrib import messages
from django.contrib.auth.models import User
from allauth.account.views import ConfirmEmailView
from allauth.account.models import EmailAddress

# Importações dos modelos e API
import requests
from partidas.models import Partida, Esporte
from quadras.models import Quadra
from social.models import Atividade
from app.feed_utils import build_activity_sections
# ✅ OTIMIZAÇÃO: As funções da API são importadas do cliente,
# não definidas localmente.
from conteudo.api_client import buscar_noticias_esportivas, buscar_clima_marica, buscar_previsao_chuva


class EsporteFYConfirmEmailView(ConfirmEmailView):
    """Sobrescreve o allauth para redirecionar ao feed com mensagem de sucesso."""
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        # Só adiciona a mensagem quando a confirmação foi bem-sucedida (redirect 3xx)
        if response.status_code in (301, 302):
            messages.success(
                self.request,
                "E-mail confirmado com sucesso! Bem-vindo ao EsporteFY!",
            )
        return response

    def get_success_url(self):
        return '/feed/'


class ResendVerificationView(LoginRequiredMixin, View):
    """Reenvia o e-mail de confirmação para o usuário autenticado."""
    def post(self, request, *args, **kwargs):
        try:
            email_address = EmailAddress.objects.get(user=request.user, primary=True, verified=False)
            email_address.send_confirmation(request)
            messages.info(request, "E-mail de confirmação reenviado. Verifique sua caixa de entrada.")
        except EmailAddress.DoesNotExist:
            messages.warning(request, "Nenhum e-mail pendente de verificação encontrado.")
        return redirect('account_email_verification_sent')


class HomeView(View):
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('feed')
        return render(request, self.template_name)

class FeedView(LoginRequiredMixin, View):
    
    template_name = 'feed.html'
    
    def get(self, request, *args, **kwargs):
        # Bloqueia acesso ao feed enquanto o e-mail não for confirmado
        if not EmailAddress.objects.filter(user=request.user, verified=True).exists():
            return redirect('account_email_verification_sent')
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
        esporte_filtrado = request.GET.get('esporte', 'todos')
        nearby_only = request.GET.get('nearby') == '1'
        data_filtro = request.GET.get('date_filter', 'all')
        custom_date_raw = request.GET.get('custom_date', '').strip()
        custom_time_raw = request.GET.get('custom_time', '').strip()
        
        # ✅ OTIMIZAÇÃO: Adicionado prefetch_related('jogadores_confirmados')
        # Isso busca todos os jogadores de todas as partidas em UMA consulta.
        partidas_list = Partida.objects.filter(
            data_hora__gte=timezone.now()
        ).select_related(
            'quadra', 'esporte', 'organizador'
        ).prefetch_related(
            'jogadores_confirmados',
            'quadra__fotos',
        ).order_by('data_hora')

        if bairro_filtrado and bairro_filtrado != 'todos':
            partidas_list = partidas_list.filter(quadra__bairro=bairro_filtrado)

        if esporte_filtrado and esporte_filtrado != 'todos':
            partidas_list = partidas_list.filter(esporte__id=esporte_filtrado)

        hoje_local = timezone.localdate()
        if data_filtro == 'today':
            partidas_list = partidas_list.filter(data_hora__date=hoje_local)
        elif data_filtro == 'tomorrow':
            partidas_list = partidas_list.filter(data_hora__date=hoje_local + timedelta(days=1))
        elif data_filtro == 'custom':
            custom_date = parse_date(custom_date_raw) if custom_date_raw else None
            custom_time = parse_time(custom_time_raw) if custom_time_raw else None
            if custom_date:
                partidas_list = partidas_list.filter(data_hora__date=custom_date)
            if custom_time:
                partidas_list = partidas_list.filter(data_hora__time__gte=custom_time)

        if nearby_only:
            partidas_list = partidas_list.exclude(organizador=request.user)
        
        context['partidas'] = partidas_list
        context['esportes_disponiveis'] = Esporte.objects.all()
        context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
        context['bairro_atual'] = bairro_filtrado
        context['bairro_atual_nome'] = dict(Quadra.BAIRRO_CHOICES).get(bairro_filtrado, 'Todos')
        context['esporte_atual'] = esporte_filtrado
        context['esporte_atual_nome'] = (
            Esporte.objects.filter(id=esporte_filtrado).values_list('nome', flat=True).first()
            if esporte_filtrado != 'todos' else 'Todos'
        ) or 'Todos'
        context['nearby_only'] = nearby_only
        context['data_filtro'] = data_filtro
        context['custom_date'] = custom_date_raw
        context['custom_time'] = custom_time_raw

        if data_filtro == 'today':
            context['data_filtro_nome'] = 'Hoje'
        elif data_filtro == 'tomorrow':
            context['data_filtro_nome'] = 'Amanhã'
        elif data_filtro == 'custom' and custom_date_raw and custom_time_raw:
            context['data_filtro_nome'] = f'{custom_date_raw} · {custom_time_raw}'
        elif data_filtro == 'custom' and custom_date_raw:
            context['data_filtro_nome'] = custom_date_raw
        elif data_filtro == 'custom' and custom_time_raw:
            context['data_filtro_nome'] = f'Após {custom_time_raw}'
        else:
            context['data_filtro_nome'] = 'Qualquer data'

        context['partidas_hoje_count'] = partidas_list.filter(data_hora__date=hoje_local).count()

        # Aproximação de presença: usuários com último login recente.
        online_threshold = timezone.now() - timedelta(minutes=30)
        context['jogadores_online_count'] = User.objects.filter(last_login__gte=online_threshold).count()

        if bairro_filtrado and bairro_filtrado != 'todos':
            context['quadras_proximas_count'] = Quadra.objects.filter(bairro=bairro_filtrado).count()
        else:
            context['quadras_proximas_count'] = Quadra.objects.count()

        
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
                print(f"❌ ERRO CRÍTICO ao pré-buscar GFK (ct_id={ct_id}, object_ids={object_ids}): {e}") 
                print(f"Traceback: ", end="")
                import traceback
                traceback.print_exc()

        # 3. Anexa os objetos pré-buscados às atividades
        # O template agora acessará o 'alvo' sem bater no banco.
        for atividade in atividades_list:
            cache_key = (atividade.content_type_id, atividade.object_id)
            atividade.alvo = content_cache.get(cache_key)
            if atividade.alvo is None:
                print(f"⚠️ AVISO: Atividade {atividade.id} ({atividade.ator.username} {atividade.verbo}) não achou objeto no cache - key: {cache_key}")

        activity_sections, activity_counts, featured_activities = build_activity_sections(
            atividades_list,
            viewer=request.user,
            available_partida_ids={partida.id for partida in partidas_list},
        )
        context['activity_sections'] = activity_sections
        context['activity_counts'] = activity_counts
        context['featured_activities'] = featured_activities
        context['atividades'] = atividades_list
        
        return context

# 🐛 CORREÇÃO: Removemos a definição local de buscar_clima_marica().
# Ela deve viver em 'conteudo/api_client.py' e ser importada (como feito acima).