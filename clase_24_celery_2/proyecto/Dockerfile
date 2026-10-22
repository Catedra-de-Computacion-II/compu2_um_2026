# Clase 24: una sola imagen para la API, los workers y Flower.
# El codigo es el mismo; lo que cambia es el 'command' de cada servicio
# en docker-compose.yml.
FROM python:3.12-slim

WORKDIR /app

# Las dependencias primero: Docker cachea esta capa y no la vuelve a
# instalar mientras requirements.txt no cambie (clase 1).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
