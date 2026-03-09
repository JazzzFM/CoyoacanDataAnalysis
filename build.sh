#!/usr/bin/env bash
# build.sh — Script de build para Render
# Instala dependencias de sistema (GDAL/GEOS/PROJ) y paquetes Python

set -o errexit

apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

pip install --upgrade pip
pip install -r requirements.txt
