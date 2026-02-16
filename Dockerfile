# Python 3.11-slim for better performance and memory management
FROM python:3.11-slim

# Install wget for downloading the ONNX model
RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory and fetch the high-quality English model at build time
RUN mkdir -p /app/models
RUN wget -O /app/models/voice.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
RUN wget -O /app/models/voice.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"

# Copy the application code
COPY . .

# Start the ASGI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
