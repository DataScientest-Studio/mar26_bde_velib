FROM python:3.12-slim

# Outils de base
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Création du venv
RUN python3 -m venv /app/.venv

# Activation du venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Installation des dépendances
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]
