FROM python:3.13-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

RUN python -m spacy download zh_core_web_md

FROM python:3.13-slim as production

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /root/.local /root/.local

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