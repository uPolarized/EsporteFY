# syntax=docker/dockerfile:1.7

# Dockerfile

# 1. Imagem Base
FROM python:3.11-slim-bookworm

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

# 3. Diretório de Trabalho
WORKDIR /app

# 3.1 Criar usuário não-root cedo para usar COPY --chown
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 4. Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar requirements primeiro
COPY requirements.txt /app/requirements.txt

# 6. Instalar dependências Python COMO ROOT

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt


# 7. Copiar o código do projeto
COPY --chown=appuser:appgroup . .

# 9. Trocar para o usuário seguro (depois de instalar tudo)
USER appuser

# 10. Expor a porta
EXPOSE 8000

# 11. Comando padrão
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
