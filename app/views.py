from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from conteudo.api_client import buscar_noticias_esportivas
from partidas.models import Partida

class HomeView(TemplateView):
    template_name = "home.html" # Assumindo que este arquivo está em app/templates/home.html

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('feed')
        return super().dispatch(request, *args, **kwargs)

class FeedView(LoginRequiredMixin, TemplateView):
    template_name = 'feed.html' # Caminho corrigido

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['noticias'] = buscar_noticias_esportivas()

        bairro_filtrado = self.request.GET.get('bairro', 'todos')
        partidas_list = Partida.objects.all()

        if bairro_filtrado and bairro_filtrado != 'todos':
            partidas_list = partidas_list.filter(bairro=bairro_filtrado)
        
        bairros_dict = dict(Partida.BAIRRO_CHOICES)
        bairro_atual_nome = bairros_dict.get(bairro_filtrado, 'Todos')

        context['partidas'] = partidas_list
        context['bairros_disponiveis'] = Partida.BAIRRO_CHOICES
        context['bairro_atual'] = bairro_filtrado
        context['bairro_atual_nome'] = bairro_atual_nome
        
        return context