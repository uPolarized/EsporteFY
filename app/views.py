from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Max
from datetime import timedelta # 1. Importa o timedelta

# Importações dos modelos e API
from conteudo.api_client import buscar_noticias_esportivas
from partidas.models import Partida
from quadras.models import Quadra
from social.models import Atividade
from conteudo.api_client import buscar_noticias_esportivas, buscar_clima_marica

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