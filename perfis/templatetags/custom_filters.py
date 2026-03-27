from django import template
import os
import time

register = template.Library()

@register.filter
def filename(value):
    """Retorna apenas o nome do arquivo de um caminho completo"""
    if value:
        return os.path.basename(str(value))
    return ''


@register.filter
def media_bust(url):
    """Adiciona query param de versão para evitar cache agressivo em mídias (ex.: GIF animado)."""
    if not url:
        return ''
    sep = '&' if '?' in str(url) else '?'
    return f"{url}{sep}v={int(time.time())}"