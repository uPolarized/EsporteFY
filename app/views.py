from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Max
from datetime import timedelta # 1. Importa o timedelta
from django.conf import settings
# Importações dos modelos e API
from conteudo.api_client import buscar_noticias_esportivas
import requests
from partidas.models import Partida
from quadras.models import Quadra
from social.models import Atividade
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
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = {}

        context['clima_atual'] = buscar_clima_marica()
        context['noticias'] = buscar_noticias_esportivas()
        context['previsao_chuva'] = buscar_previsao_chuva()

        uma_semana_atras = timezone.now() - timedelta(days=7)


        
        # 3. Busca apenas as atividades que aconteceram DEPOIS daquela data
        context['atividades'] = Atividade.objects.filter(
            timestamp__gte=uma_semana_atras
        ).select_related('ator__perfil')[:20]
        
        bairro_filtrado = self.request.GET.get('bairro', 'todos')
        partidas_list = Partida.objects.filter(data_hora__gte=timezone.now()).select_related('quadra')
        if bairro_filtrado and bairro_filtrado != 'todos':
            partidas_list = partidas_list.filter(quadra__bairro=bairro_filtrado)
        
        context['partidas'] = partidas_list
        context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
        context['bairro_atual'] = bairro_filtrado
        context['bairro_atual_nome'] = dict(Quadra.BAIRRO_CHOICES).get(bairro_filtrado, 'Todos')

        
        # Lógica do Feed de Atividades
        # 1. Calcula a data de 7 dias atrás a partir de hoje
        uma_semana_atras = timezone.now() - timedelta(days=7)

        context['atividades'] = Atividade.objects.filter(
            timestamp__gte=uma_semana_atras
        ).select_related('ator__perfil')[:20]
        
        return context
    
def buscar_clima_marica():
    """
    Busca o clima atual em Maricá (RJ) usando a API OpenWeatherMap.
    Retorna um dicionário com temperatura, descrição, ícone e mensagem personalizada.
    """
    try:
        api_key = settings.OPENWEATHER_API_KEY
        cidade = "Maricá"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={cidade},BR&appid={api_key}&lang=pt_br&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        dados = response.json()

        descricao = dados["weather"][0]["description"].capitalize()
        temperatura = round(dados["main"]["temp"])
        icone = dados["weather"][0]["icon"]

        # 💬 Gera mensagem personalizada baseada na descrição
        desc_lower = descricao.lower()
        if "chuva forte" in desc_lower or "tempestade" in desc_lower:
            mensagem = "⛈️ Chuva pesada chegando! Melhor optar por quadras cobertas ou descansar hoje."
        elif "chuva" in desc_lower:
            mensagem = "🌧️ Pode chover hoje. Prefira quadras cobertas!"
        elif "nublado" in desc_lower:
            mensagem = "☁️ O clima está fechado, mas ainda dá pra jogar tranquilo. Leve um agasalho leve."
        elif "limpo" in desc_lower or "ensolarado" in desc_lower:
            mensagem = "☀️ Ótimo dia para jogar bola! Lembre-se de beber água e usar protetor solar. 💧🧴"
        elif "neblina" in desc_lower:
            mensagem = "🌫️ Atenção com a visibilidade! Evite quadras muito abertas."
        elif "vento" in desc_lower:
            mensagem = "💨 Dia de ventania! Pode ser difícil controlar a bola em campo aberto."
        else:
            mensagem = "🌤️ Tempo agradável! Perfeito para jogar com os amigos."

        return {
            "temperatura": temperatura,
            "descricao": descricao,
            "icone": icone,
            "mensagem": mensagem,  # 👈 ESSENCIAL
        }

    except Exception as e:
        print(f"[ERRO] Falha ao buscar clima de Maricá: {e}")
        return None
