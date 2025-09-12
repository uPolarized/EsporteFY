from django.shortcuts import render
from django.views.generic import UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Perfil
from .forms import PerfilForm

class PerfilView(LoginRequiredMixin, DetailView):
    model = Perfil
    template_name = 'perfis/perfil.html'

    def get_object(self):
        return self.request.user.perfil

class EditarPerfilView(LoginRequiredMixin, UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'perfis/editar_perfil.html'
    success_url = reverse_lazy('perfil')

    def get_object(self):
        return self.request.user.perfil