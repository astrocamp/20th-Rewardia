FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN python -m spacy download zh_core_web_md

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY . /app/

COPY .pg_service.conf /app/.pg_service.conf
COPY .pg_db_pass /app/.pg_db_pass
RUN chmod 600 /app/.pg_db_pass
ENV PGSERVICEFILE=/app/.pg_service.conf
ENV PGPASSFILE=/app/.pg_db_pass

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /var/log/supervisor

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]