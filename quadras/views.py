# quadras/views.py
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Quadra
from .serializers import QuadraSerializer

class QuadraListAPIView(generics.ListAPIView):
    """
    Endpoint completo da API de Quadras.
    Suporta busca, filtros e paginação automática.
    """
    queryset = Quadra.objects.prefetch_related('fotos').order_by('nome')
    serializer_class = QuadraSerializer

    # Filtros e busca habilitados
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bairro']  # Ex: /api/quadras/?bairro=itaipuaçu
    search_fields = ['nome', 'descricao', 'bairro']  # Ex: /api/quadras/?search=arena
    ordering_fields = ['nome', 'bairro']
