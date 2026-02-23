from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from piper.voice import PiperVoice
import os
import uuid
import wave
import logging

# ==========================
# CONFIGURATION
# ==========================

MODEL_PATH = "/app/models/voice.onnx"
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("piper-tts")

# In-memory model storage
ml_models = {}

# ==========================
# APP LIFESPAN
# ==========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up: Loading Piper TTS Model...")

    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

        ml_models["voice"] = PiperVoice.load(MODEL_PATH)

        if not ml_models["voice"]:
            raise RuntimeError("Model loaded as None")

        logger.info("✅ Model loaded successfully into memory!")

    except Exception as e:
        logger.critical(f"❌ Failed to load model: {e}")
        ml_models["voice"] = None

    yield

    logger.info("🧹 Shutting down: Clearing memory...")
    ml_models.clear()


# ==========================
# FASTAPI INIT
# ==========================

app = FastAPI(
    title="Piper TTS Microservice",
    version="1.5.0",
    lifespan=lifespan
)


# ==========================
# REQUEST SCHEMA
# ==========================

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


# ==========================
# CLEANUP FUNCTION
# ==========================

def cleanup_file(filepath: str):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"🗑️ Cleanup done: {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to delete {filepath}: {e}")


# ==========================
# ROUTES
# ==========================

@app.get("/health")
def health_check():
    if not ml_models.get("voice"):
        raise HTTPException(status_code=503, detail="Model is not loaded properly.")

    return {
        "status": "ok",
        "message": "Piper TTS Worker running smoothly 🚀"
    }


@app.post("/generate-audio")
async def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):

    voice_model = ml_models.get("voice")

    if not voice_model:
        raise HTTPException(status_code=500, detail="TTS Model is not initialized.")

    session_id = str(uuid.uuid4())
    output_filepath = os.path.join(TEMP_DIR, f"voiceover_{session_id}.wav")

    try:
        logger.info(f"🎙️ Generating audio for text length: {len(request.text)}")

        with wave.open(output_filepath, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)

            # Safe sample rate fallback
            sample_rate = getattr(
                voice_model.config,
                "sample_rate",
                22050
            )
            wav_file.setframerate(sample_rate)

            voice_model.synthesize(request.text, wav_file)

        background_tasks.add_task(cleanup_file, output_filepath)

        return FileResponse(
            output_filepath,
            media_type="audio/wav",
            filename=f"voiceover_{session_id[:8]}.wav"
        )

    except Exception as e:
        cleanup_file(output_filepath)
        logger.error(f"❌ Audio generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Audio generation failed."
        )
