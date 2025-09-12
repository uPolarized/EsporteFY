from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(TemplateView):
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        # Se o usuário que acessa a homepage já estiver autenticado,
        # redireciona-o para a página de feed.
        if request.user.is_authenticated:
            return redirect('feed')
        # Se não estiver autenticado, continua normalmente e mostra a homepage.
        return super().dispatch(request, *args, **kwargs)


class FeedView(LoginRequiredMixin, TemplateView):
    template_name = 'feed.html'