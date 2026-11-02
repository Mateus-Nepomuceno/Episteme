FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY turma ./turma
COPY migrations ./migrations

RUN pip install --no-cache-dir .

CMD ["sh", "-c", "alembic upgrade head && if [ \"$SEED\" = \"1\" ]; then python -m turma.seed; fi && exec uvicorn turma.app:app --host 0.0.0.0 --port 8000"]
