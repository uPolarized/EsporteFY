import requests
from django.conf import settings
from urllib.parse import quote
from django.core.cache import cache

def buscar_noticias_esportivas():
    """
    Busca notícias focadas em futebol (Brasileirão, Copa do Brasil, Champions League).
    """
    cache_key = 'noticias_futebol_feed' # Novo nome de cache para a nova busca
    noticias_cacheadas = cache.get(cache_key)
    
    if noticias_cacheadas is not None:
        print("Notícias (futebol) carregadas do cache.")
        return noticias_cacheadas

    print("Cache vazio. Buscando notícias de futebol na API...")
    api_key = settings.NEWS_API_KEY
    if not api_key:
        return []

    # --- CONSULTA SUPER FOCADA E SIMPLES ---
    keywords = [
        '"Brasileirão"',
        '"Copa do Brasil"',
        '"Champions League"',
    ]
    query_string = " OR ".join(keywords)
    
    url = (
        'https://newsapi.org/v2/everything?'
        f'q={quote(query_string)}&'  # Busca pelos termos principais
        'language=pt&'
        'sortBy=publishedAt&' # Ordena pelos mais recentes
        f'apiKey={api_key}'
    )
    # ------------------------------------

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        articles_brutos = data.get('articles', [])
        artigos_filtrados = [
            artigo for artigo in articles_brutos 
            if artigo.get('title') and '[Removed]' not in artigo.get('title')
        ]
        
        noticias_finais = artigos_filtrados[:10]
        cache.set(cache_key, noticias_finais, timeout=3600) # Cache de 1 hora
        return noticias_finais

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar notícias: {e}")
        return []