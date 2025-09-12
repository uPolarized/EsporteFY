from django.views.generic import TemplateView # Mude ListView para TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from conteudo.api_client import buscar_noticias_esportivas # Importe nossa nova função

class HomeView(TemplateView):
    template_name = "home.html"

class FeedView(LoginRequiredMixin, TemplateView):
    template_name = 'feed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Chama a função da API e adiciona as notícias ao contexto do template
        context['noticias'] = buscar_noticias_esportivas()
        return context