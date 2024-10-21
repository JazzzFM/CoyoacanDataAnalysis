# Dockerfile

# Usar una imagen base oficial de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requisitos y luego instalar las dependencias
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instalar rtree para índices espaciales
RUN pip install --no-cache-dir rtree

# Copiar el resto de los archivos de la aplicación
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 8050

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
