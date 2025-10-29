from django.http import JsonResponse
from .models import Quadra

def api_lista_quadras(request):
    """
    Uma view 'API' que retorna todas as quadras em formato JSON
    para serem consumidas pelo mapa Leaflet.js.
    """
    quadras_list = []
    
    # Usamos prefetch_related para otimizar a busca da foto principal
    quadras = Quadra.objects.all().prefetch_related('fotos').order_by('nome')

    for quadra in quadras:
        # Só inclui quadras que têm localização definida
        if quadra.latitude and quadra.longitude:
            
            foto_url = None
            foto_principal = quadra.foto_principal() # Chama o método do seu model
            if foto_principal and hasattr(foto_principal.imagem, 'url'):
                foto_url = foto_principal.imagem.url

            quadras_list.append({
                'id': quadra.id,
                'nome': quadra.nome,
                'bairro': quadra.get_bairro_display(),
                'latitude': quadra.latitude,
                'longitude': quadra.longitude,
                'foto_url': foto_url
            })

    return JsonResponse({'quadras': quadras_list})