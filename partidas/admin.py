from django.contrib import admin

from .models import PartidaRSVP

# Register your models here.


@admin.register(PartidaRSVP)
class PartidaRSVPAdmin(admin.ModelAdmin):
	list_display = ('partida', 'jogador', 'status', 'lembrete_24h_enviado', 'atualizado_em')
	list_filter = ('status', 'lembrete_24h_enviado', 'atualizado_em')
	search_fields = ('partida__titulo', 'jogador__username', 'motivo_recusa')
