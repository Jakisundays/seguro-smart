# Usa una imagen base de Python
FROM python:3.11-slim

# Install system dependencies (optional, for common Python packages)
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . . 

# Expone el puerto que usa Streamlit (por defecto es 8501)
EXPOSE 8888

# Comando para ejecutar la aplicación Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8888", "--server.address=0.0.0.0", "--server.enableCORS=false"]

