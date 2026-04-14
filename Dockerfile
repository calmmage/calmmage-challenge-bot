FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --group extras --frozen || uv sync --group extras

COPY . .

RUN mkdir -p sessions

CMD ["uv", "run", "python", "src/bot.py"]
