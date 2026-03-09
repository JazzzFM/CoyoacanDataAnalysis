# Dockerfile — Compatible con Render (Docker deploy)

FROM python:3.11-slim

WORKDIR /app

# Dependencias de sistema para GeoPandas (GDAL/GEOS/PROJ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Render asigna $PORT dinámicamente
EXPOSE 8050

CMD gunicorn --bind 0.0.0.0:${PORT:-8050} --timeout 120 --workers 2 run:app
