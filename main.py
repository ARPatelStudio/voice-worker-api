from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from piper.voice import PiperVoice
import os
import uuid

# Define constants
MODEL_PATH = "/app/models/voice.onnx"
TEMP_DIR = "/tmp"

# Global dictionary to maintain ML models in memory
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for handling startup and shutdown events.
    Loads the Piper TTS model into memory on startup and clears it on shutdown.
    """
    print("🚀 Starting up: Loading Piper TTS Model...")
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        ml_models["voice"] = PiperVoice.load(MODEL_PATH)
        print("✅ Model loaded successfully into memory!")
    except Exception as e:
        print(f"❌ Critical Error loading model: {e}")
        ml_models["voice"] = None
        
    yield 
    
    print("🧹 Shutting down: Clearing memory...")
    ml_models.clear()

# Initialize FastAPI application
app = FastAPI(title="Piper TTS Microservice", version="1.4.1", lifespan=lifespan)

# Pydantic schema for request validation
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to synthesize into speech.")

def cleanup_file(filepath: str):
    """
    Background task to delete the temporary audio file after the response is sent.
    """
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🗑️ Cleanup done: {filepath}")
        except Exception as e:
            print(f"❌ Failed to delete {filepath}: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint to verify model readiness."""
    if not ml_models.get("voice"):
        raise HTTPException(status_code=503, detail="Model is not loaded properly.")
    return {"status": "ok", "message": "Piper TTS Worker is running seamlessly."}

@app.post("/generate-audio")
async def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generates a .wav audio file from the provided text using the pre-loaded Piper TTS model.
    """
    voice_model = ml_models.get("voice")
    
    # Edge Case: Model failed to load during startup
    if not voice_model:
        raise HTTPException(status_code=500, detail="TTS Model is not initialized.")
    
    # Generate unique filename for concurrency safety
    session_id = str(uuid.uuid4())
    output_filepath = os.path.join(TEMP_DIR, f"voiceover_{session_id}.wav")

    try:
        print(f"🎙️ Synthesizing audio for: '{request.text[:40]}...'")
        
        # Write synthesized audio to the temporary file
        with open(output_filepath, "wb") as wav_file:
            voice_model.synthesize(request.text, wav_file)

        # Schedule the cleanup task
        background_tasks.add_task(cleanup_file, output_filepath)

        # Return the generated audio file
        return FileResponse(
            output_filepath, 
            media_type="audio/wav", 
            filename=f"voiceover_{session_id[:8]}.wav"
        )

    except Exception as e:
        # Error Handling: Ensure cleanup happens even if synthesis fails
        cleanup_file(output_filepath)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
