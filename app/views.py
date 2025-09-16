from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from conteudo.api_client import buscar_noticias_esportivas
from partidas.models import Partida
from django.utils import timezone
from quadras.models import Quadra

class HomeView(TemplateView):
    template_name = "home.html" # Assumindo que este arquivo está em app/templates/home.html

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('feed')
        return super().dispatch(request, *args, **kwargs)

class FeedView(LoginRequiredMixin, TemplateView):
    template_name = 'feed.html' # <-- Correto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['noticias'] = buscar_noticias_esportivas()

        bairro_filtrado = self.request.GET.get('bairro', 'todos')
        partidas_list = Partida.objects.filter(data_hora__gte=timezone.now()).select_related('quadra')

        if bairro_filtrado and bairro_filtrado != 'todos':
            partidas_list = partidas_list.filter(quadra__bairro=bairro_filtrado)
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Pega as opções de bairro do modelo Quadra, que é o local correto agora
        bairros_dict = dict(Quadra.BAIRRO_CHOICES)
        context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
        # -------------------------------
        
        bairro_atual_nome = bairros_dict.get(bairro_filtrado, 'Todos')

        context['partidas'] = partidas_list
        context['bairro_atual'] = bairro_filtrado
        context['bairro_atual_nome'] = bairro_atual_nome
        
        return context