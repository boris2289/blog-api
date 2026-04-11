FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    netcat-openbsd \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements

RUN useradd -u 2283 boris

RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

RUN mkdir -p /app/data
RUN mkdir -p /app/data /app/logs && chown -R boris:boris /app
RUN chmod +x /app/scripts/entrypoint.sh

ENTRYPOINT ["/app/scripts/entrypoint.sh"]

USER boris