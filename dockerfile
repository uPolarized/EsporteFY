# Dockerfile

# 1. Imagem Base
FROM python:3.11-slim-bookworm

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Diretório de Trabalho
WORKDIR /app

# 4. Instalar Dependências
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# 5. Copiar o Código do Projeto
COPY . .

# 6. Criar utilizador não-root para segurança
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# 7. Expor a porta que a aplicação vai usar
EXPOSE 8000