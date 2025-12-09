from django.contrib import admin
from .models import Quadra, FotoQuadra

# Esta classe permite-nos editar as Fotos diretamente na página da Quadra
class FotoQuadraInline(admin.TabularInline):
    model = FotoQuadra
    extra = 1  # Quantos campos de upload de foto extra aparecem

@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'bairro')
    list_filter = ('bairro',)
    search_fields = ('nome', 'descricao')
    # Adiciona a secção de fotos à página de edição da Quadra
    inlines = [FotoQuadraInline]

# Também registamos o modelo FotoQuadra para que possa ser gerido separadamente, se necessário
admin.site.register(FotoQuadra)
