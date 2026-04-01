import requests
from django.conf import settings
from urllib.parse import quote
from django.core.cache import cache
from datetime import datetime


EXTERNAL_API_TIMEOUT_SECONDS = 2.5


def buscar_noticias_esportivas():
    """
    Busca notícias focadas em futebol (Brasileirão, Copa do Brasil, Champions League).
    """
    cache_key = 'noticias_futebol_feed'
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
        response = requests.get(url, timeout=EXTERNAL_API_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        
        articles_brutos = data.get('articles', [])
        artigos_filtrados = [
            artigo for artigo in articles_brutos 
            if artigo.get('title') and '[Removed]' not in artigo.get('title')
        ]
        
        noticias_finais = artigos_filtrados[:10]
        cache.set(cache_key, noticias_finais, timeout=3600)
        return noticias_finais

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar notícias: {e}")
        return []
    

def buscar_clima_marica():
    """
    Busca o clima atual em Maricá (RJ) usando a API OpenWeatherMap.
    Retorna um dicionário com temperatura, descrição, ícone e mensagem personalizada.
    """
    cache_key = 'clima_marica'
    clima_cacheado = cache.get(cache_key)
    if clima_cacheado is not None:
        return clima_cacheado

    try:
        api_key = settings.OPENWEATHER_API_KEY
        if not api_key:
            return None
        cidade = "Maricá"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={cidade},BR&appid={api_key}&lang=pt_br&units=metric"
        response = requests.get(url, timeout=EXTERNAL_API_TIMEOUT_SECONDS)
        response.raise_for_status()
        dados = response.json()

        descricao = dados["weather"][0]["description"].capitalize()
        temperatura = round(dados["main"]["temp"])
        icone = dados["weather"][0]["icon"]

        # 💬 Gera mensagem personalizada baseada na descrição
        desc_lower = descricao.lower()
        if "chuva forte" in desc_lower or "tempestade" in desc_lower:
            mensagem = "⛈️ Chuva pesada chegando! Melhor optar por quadras cobertas ou descansar hoje."
        elif "chuva" in desc_lower:
            mensagem = "🌧️ Pode chover hoje. Prefira quadras cobertas!"
        elif "nublado" in desc_lower:
            mensagem = "☁️ O clima está fechado, mas ainda dá pra jogar tranquilo. Leve um agasalho leve."
        elif "limpo" in desc_lower or "ensolarado" in desc_lower:
            mensagem = "☀️ Ótimo dia para jogar bola! Lembre-se de beber água e usar protetor solar. 💧🧴"
        elif "neblina" in desc_lower:
            mensagem = "🌫️ Atenção com a visibilidade! Evite quadras muito abertas."
        elif "vento" in desc_lower:
            mensagem = "💨 Dia de ventania! Pode ser difícil controlar a bola em campo aberto."
        else:
            mensagem = "🌤️ Tempo agradável! Perfeito para jogar com os amigos."

        payload = {
            "temperatura": temperatura,
            "descricao": descricao,
            "icone": icone,
            "mensagem": mensagem,  # 👈 ESSENCIAL
        }
        cache.set(cache_key, payload, timeout=600)
        return payload

    except Exception as e:
        print(f"[ERRO] Falha ao buscar clima de Maricá: {e}")
        return None

    
def buscar_previsao_chuva():
    """Verifica se há previsão de chuva hoje em Maricá (com base na API OpenWeather)."""
    cache_key = 'previsao_chuva_marica'
    previsao_cacheada = cache.get(cache_key)
    if previsao_cacheada is not None:
        return previsao_cacheada

    try:
        api_key = settings.OPENWEATHER_API_KEY
        if not api_key:
            return {"vai_chover": False, "chuva_mm": 0}
        url = f"https://api.openweathermap.org/data/2.5/forecast?q=Maricá,BR&appid={api_key}&lang=pt_br&units=metric"
        response = requests.get(url, timeout=EXTERNAL_API_TIMEOUT_SECONDS)
        response.raise_for_status()
        dados = response.json()

        hoje = datetime.now().date()
        vai_chover = False
        chuva_mm = 0

        for entrada in dados["list"]:
            data_prev = datetime.fromtimestamp(entrada["dt"]).date()
            if data_prev == hoje:
                if "rain" in entrada and entrada["rain"].get("3h", 0) > 0:
                    vai_chover = True
                    chuva_mm += entrada["rain"]["3h"]

        payload = {
            "vai_chover": vai_chover,
            "chuva_mm": round(chuva_mm, 1)
        }
        cache.set(cache_key, payload, timeout=600)
        return payload

    except Exception as e:
        print(f"[ERRO] Previsão de chuva: {e}")
        return {"vai_chover": False, "chuva_mm": 0}