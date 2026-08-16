FROM python:3.13.0-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN uv sync --frozen --no-dev \
    && groupadd --system telescan \
    && useradd --system --gid telescan --home-dir /app telescan \
    && mkdir -p /data \
    && chown -R telescan:telescan /app /data

USER telescan

CMD ["uv", "run", "--no-dev", "run_polling.py"]
