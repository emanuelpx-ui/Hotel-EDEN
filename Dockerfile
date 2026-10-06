# Usa una imagen ligera de Python
FROM python:3.14-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requerimientos e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Expone el puerto que usa Flask (usualmente 5000)
EXPOSE 5000

# Comando para ejecutar la aplicación (puedes ajustarlo si usas Gunicorn en procfile)
CMD ["python", "app.py"]