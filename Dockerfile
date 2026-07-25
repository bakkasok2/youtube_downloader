FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    MAX_DOWNLOAD_MB=500 \
    DOWNLOAD_TIMEOUT_SECONDS=900 \
    DENO_INSTALL=/usr/local

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg git unzip \
    && curl -fsSL https://deno.land/install.sh | sh \
    && git clone --depth 1 --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /root/bgutil-ytdlp-pot-provider \
    && cd /root/bgutil-ytdlp-pot-provider/server \
    && deno install --allow-scripts=npm:canvas --frozen \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 900 app:app"]
