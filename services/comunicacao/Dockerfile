FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.5.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

WORKDIR /app

# Instala o Poetry em ambiente isolado para nao contaminar o ambiente Python da aplicacao
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Camada de dependencias: copia apenas arquivos de definicao e lock para otimizar cache
COPY pyproject.toml poetry.lock README.md alembic.ini ./

# Instala estritamente as dependencias de producao travadas no poetry.lock, sem grupo dev
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Camada da aplicacao: codigo-fonte e migracoes
COPY comunicacao ./comunicacao
COPY migrations ./migrations

# Instala o pacote do proprio microsservico
RUN poetry install --only main --no-interaction --no-ansi

CMD ["sh", "-c", "alembic upgrade head && if [ \"$SEED\" = \"1\" ]; then python -m comunicacao.seed; fi && exec uvicorn comunicacao.app:app --host 0.0.0.0 --port 8000"]


