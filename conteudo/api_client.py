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
        '"Maricá"'
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
    

def buscar_clima_marica():
    """
    Busca os dados do clima atual para Maricá com mensagens de depuração.
    """
    cache_key = 'clima_marica_atual'
    clima_cache = cache.get(cache_key)
    if clima_cache:
        print("DEBUG (Clima): Dados do clima carregados do CACHE.")
        return clima_cache

    print("DEBUG (Clima): Cache vazio. A tentar buscar na API do OpenWeather...")
    
    # Verifica se a chave da API foi carregada do .env para o settings.py
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
    if not api_key:
        print("DEBUG (Clima): ERRO - OPENWEATHER_API_KEY não foi encontrada nas configurações!")
        return None

    city_id = '3457963' # ID de Maricá
    url = (
        'https://api.openweathermap.org/data/2.5/weather?'
        f'id={city_id}&'
        f'appid={api_key}&'
        'lang=pt_br&'
        'units=metric'
    )

    print("DEBUG (Clima): A aceder à URL da API...")

    try:
        response = requests.get(url, timeout=10)
        print(f"DEBUG (Clima): Resposta da API recebida. Status Code: {response.status_code}")
        
        # Lança um erro para códigos 4xx/5xx (ex: 401 para chave inválida)
        response.raise_for_status() 
        data = response.json()

        clima = {
            'temperatura': round(data['main']['temp']),
            'descricao': data['weather'][0]['description'].capitalize(),
            'icone': data['weather'][0]['icon'],
        }
        
        cache.set(cache_key, clima, timeout=600) # Cache de 10 minutos
        print("DEBUG (Clima): Dados do clima obtidos e guardados em cache com sucesso.")
        return clima
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            print("DEBUG (Clima): ERRO CRÍTICO - A sua chave da API do OpenWeather é INVÁLIDA ou está desativada. (Erro 401 Unauthorized)")
        else:
            print(f"DEBUG (Clima): ERRO HTTP ao aceder à API: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"DEBUG (Clima): ERRO CRÍTICO de conexão à API: {e}")
        return None