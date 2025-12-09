from django import template
import os

register = template.Library()

@register.filter
def filename(value):
    """Retorna apenas o nome do arquivo de um caminho completo"""
    if value:
        return os.path.basename(str(value))
    return ''