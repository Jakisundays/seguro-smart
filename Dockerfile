# Usa una imagen base de Python
FROM python:3.11-slim

# Install system dependencies (optional, for common Python packages)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . . 

# Expone los puertos que usan las aplicaciones Streamlit
EXPOSE 8010 8011

# Comando por defecto (se puede sobrescribir en docker-compose)
CMD ["streamlit", "run", "app.py", "--server.port=8010", "--server.address=0.0.0.0"]