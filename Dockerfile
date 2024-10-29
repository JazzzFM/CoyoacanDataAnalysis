# Dockerfile

# Usar una imagen base de Python optimizada
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Modificar Flask-Login para usar funciones compatibles de Werkzeug
RUN sed -i \
    -e "s/from werkzeug.urls import url_decode/from urllib.parse import unquote as url_decode/g" \
    -e "s/from werkzeug.urls import url_encode/from urllib.parse import quote as url_encode/g" \
    /usr/local/lib/python3.9/site-packages/flask_login/utils.py

# Copiar el resto del código de la aplicación
COPY . .

# Asegurarse de que wait-for-it.sh tenga permisos de ejecución
RUN chmod +x wait-for-it.sh

# Exponer el puerto que usará la aplicación
EXPOSE 8050

# Comando para iniciar la aplicación con wait-for-it.sh y Gunicorn
CMD ["./wait-for-it.sh", "db:5432", "--", "gunicorn", "--bind", "0.0.0.0:8050", "run:app"]

