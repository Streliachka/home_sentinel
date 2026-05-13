FROM python:3.11-slim

RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Отключаем телеметрию и ставим дефолтный адрес (который можно перебить при старте)
# Example docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 --add-host=host.docker.internal:host-gateway sentinel-app
ENV CREWAI_TELEMETRY_OPT_OUT=true
ENV OLLAMA_BASE_URL=http://localhost:11434

CMD ["python", "main.py"]