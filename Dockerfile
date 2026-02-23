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

# Create models directory
RUN mkdir -p /app/models

# Download 4 Voices
RUN wget -O /app/models/ryan.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx?download=true"
RUN wget -O /app/models/ryan.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json?download=true"
RUN wget -O /app/models/amy.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true"
RUN wget -O /app/models/amy.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true"
RUN wget -O /app/models/lessac.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
RUN wget -O /app/models/lessac.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"
RUN wget -O /app/models/alan.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx?download=true"
RUN wget -O /app/models/alan.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json?download=true"

# 🎵 NAYA: Download Royalty-Free Suspense Background Music
RUN wget -O /app/suspense_bgm.ogg "https://upload.wikimedia.org/wikipedia/commons/2/25/Dark_Ambient_Loop.ogg"

# Copy the application code
COPY . .

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
