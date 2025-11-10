# quadras/serializers.py
from rest_framework import serializers
from .models import Quadra, FotoQuadra

class FotoQuadraSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoQuadra
        fields = ['id', 'imagem']

class QuadraSerializer(serializers.ModelSerializer):
    fotos = FotoQuadraSerializer(many=True, read_only=True)
    bairro_nome = serializers.CharField(source='get_bairro_display', read_only=True)
    foto_principal_url = serializers.SerializerMethodField()

    class Meta:
        model = Quadra
        fields = [
            'id', 'nome', 'bairro', 'bairro_nome',
            'descricao', 'latitude', 'longitude',
            'fonte', 'foto_principal_url', 'fotos'
        ]

    def get_foto_principal_url(self, obj):
        foto = obj.foto_principal()
        return foto.imagem.url if foto and hasattr(foto.imagem, 'url') else None
