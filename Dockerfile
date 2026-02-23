# Python 3.11-slim for better performance
FROM python:3.11-slim

# Install wget
RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory and fetch the HIGH-QUALITY US ENGLISH MALE VOICE (Ryan)
RUN mkdir -p /app/models
RUN wget -O /app/models/voice.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx?download=true"
RUN wget -O /app/models/voice.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json?download=true"

# Copy the application code
COPY . .

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
