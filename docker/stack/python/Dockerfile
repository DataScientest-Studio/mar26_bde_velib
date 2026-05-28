FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Venv
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Dépendances Python
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /workspace

# Par défaut on garde le container vivant (utile pour le service "python" de debug)
CMD ["tail", "-f", "/dev/null"]
