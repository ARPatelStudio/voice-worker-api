# Python 3.11-slim for better performance
FROM python:3.11-slim

# Install wget aur ffmpeg (Audio jodne ke liye zaroori)
RUN apt-get update && \
    apt-get install -y wget ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory aur 4 voices download karna
RUN mkdir -p /app/models

# Voice 1: Ryan (US Male - Deep/Narrator)
RUN wget -O /app/models/ryan.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx?download=true"
RUN wget -O /app/models/ryan.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json?download=true"

# Voice 2: Amy (US Female - Clear/Character)
RUN wget -O /app/models/amy.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true"
RUN wget -O /app/models/amy.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true"

# Voice 3: Lessac (US Female 2 - Professional/AI)
RUN wget -O /app/models/lessac.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
RUN wget -O /app/models/lessac.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"

# Voice 4: Alan (British Male - Villain/Scientist)
RUN wget -O /app/models/alan.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx?download=true"
RUN wget -O /app/models/alan.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json?download=true"

# Copy the application code
COPY . .

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
