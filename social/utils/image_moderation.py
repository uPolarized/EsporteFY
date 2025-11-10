# social/utils/image_moderation.py
import traceback
from google.cloud import vision
import time
# Mapeamento (caso a API retorne strings ou enums)
LIKELIHOOD_MAP = {
    "UNKNOWN": 0,
    "VERY_UNLIKELY": 1,
    "UNLIKELY": 2,
    "POSSIBLE": 3,
    "LIKELY": 4,
    "VERY_LIKELY": 5,
    # caso já seja int, mantemos
}

def _to_int(value):
    """Converte retorno do Vision (enum/string/int) para int 0-5."""
    try:
        # se for enum-like com .name
        if hasattr(value, "name"):
            return LIKELIHOOD_MAP.get(value.name, int(value))
        # se for string
        if isinstance(value, str):
            return LIKELIHOOD_MAP.get(value.upper(), int(value))
        # se já for int
        return int(value)
    except Exception:
        return 0

# Mapa de interpretação dos níveis do Vision API
SAFESEARCH_LEVELS = {
    1: "VERY_UNLIKELY",
    2: "UNLIKELY",
    3: "POSSIBLE",
    4: "LIKELY",
    5: "VERY_LIKELY",
}

def analisar_imagem(path_imagem):
    """
    Analisa a imagem com o Google Cloud Vision SafeSearch.
    Retorna (is_safe, details) e exibe logs detalhados no terminal.
    """
    print("\n" + "=" * 80)
    print(f"🧠 INICIANDO ANÁLISE DE IMAGEM → {path_imagem}")
    start_time = time.time()

    try:
        client = vision.ImageAnnotatorClient()
        with open(path_imagem, "rb") as img_file:
            content = img_file.read()

        image = vision.Image(content=content)
        response = client.safe_search_detection(image=image)
        safe = response.safe_search_annotation

        # Converter para escala numérica (1–5)
        scores = {
            "adult": safe.adult,
            "racy": safe.racy,
            "violence": safe.violence,
            "medical": safe.medical,
            "spoof": safe.spoof,
        }

        print("\n🔍 RESULTADOS SAFESEARCH (Google Vision):")
        print("-" * 80)
        for categoria, valor in scores.items():
            descricao = SAFESEARCH_LEVELS.get(valor, "UNKNOWN")
            print(f"🩸 {categoria.upper():<10} → Nível: {valor} ({descricao})")

        # Critérios de bloqueio ajustados
        bloqueios = []
        if scores["adult"] >= 4:
            bloqueios.append("Conteúdo sexual explícito (adult >= 4)")
        if scores["racy"] >= 4:
            bloqueios.append("Imagem muito provocante (racy >= 4)")
        if scores["violence"] >= 4:
            bloqueios.append("Violência gráfica (violence >= 4)")
        if scores["medical"] >= 5:
            bloqueios.append("Imagem médica explícita (medical >= 5)")

        # Resultado final
        tempo_execucao = round(time.time() - start_time, 2)
        print("-" * 80)
        if not bloqueios:
            print(f"✅ RESULTADO FINAL: IMAGEM SEGURA ({tempo_execucao}s)")
        else:
            print(f"🚫 RESULTADO FINAL: IMAGEM BLOQUEADA ({tempo_execucao}s)")
            print("🔎 MOTIVOS:")
            for motivo in bloqueios:
                print(f"   - {motivo}")

        print("=" * 80 + "\n")

        return len(bloqueios) == 0, {
            "scores": scores,
            "interpretacao": {k: SAFESEARCH_LEVELS.get(v, "?") for k, v in scores.items()},
            "insecure_reasons": bloqueios,
            "tempo_execucao": tempo_execucao,
        }

    except Exception as e:
        print("❌ ERRO AO ANALISAR IMAGEM:", e)
        print("=" * 80 + "\n")
        return True, {"error": str(e)}