FROM python:3.14-slim AS base
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl pkg-config python3-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry && pip cache purge
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --only=main --no-interaction --no-ansi --no-root

COPY . .

FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
