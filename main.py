from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from piper.voice import PiperVoice
import os
import uuid
import wave

# Define constants
MODEL_PATH = "/app/models/voice.onnx"
TEMP_DIR = "/tmp"

# Initialize FastAPI application
app = FastAPI(title="Piper TTS Microservice", version="1.4.4")

# Pydantic schema for request validation
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to synthesize into speech.")

def cleanup_file(filepath: str):
    """Background task to delete the temporary audio file after the response is sent."""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🗑️ Cleanup done: {filepath}")
        except Exception as e:
            print(f"❌ Failed to delete {filepath}: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint to verify model file exists."""
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=503, detail="Model file not found.")
    return {"status": "ok", "message": "Piper TTS Worker is ready."}

@app.post("/generate-audio")
def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generates a .wav audio file from the provided text using raw PCM streams.
    This completely bypasses the Piper/Wave conflict.
    """
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=500, detail="TTS Model file is missing.")
    
    session_id = str(uuid.uuid4())
    output_filepath = os.path.join(TEMP_DIR, f"voiceover_{session_id}.wav")

    try:
        print(f"🚀 Loading Piper Model for request...")
        voice_model = PiperVoice.load(MODEL_PATH)
        
        print(f"🎙️ Synthesizing audio for: '{request.text[:40]}...'")
        
        # FIX: Ask Piper for Raw Audio Data instead of letting it write the file
        audio_stream = voice_model.synthesize_stream_raw(request.text)
        
        # Manually construct a perfect WAV file
        with wave.open(output_filepath, "wb") as wav_file:
            wav_file.setnchannels(1)  # 1 channel (Mono)
            wav_file.setsampwidth(2)  # 2 bytes (16-bit audio)
            wav_file.setframerate(voice_model.config.sample_rate)  # Native sample rate
            
            # Write raw audio frames safely
            for pcm_chunk in audio_stream:
                wav_file.writeframes(pcm_chunk)

        # Schedule the cleanup task
        background_tasks.add_task(cleanup_file, output_filepath)

        # Return the generated audio file
        return FileResponse(
            output_filepath, 
            media_type="audio/wav", 
            filename=f"voiceover_{session_id[:8]}.wav"
        )

    except Exception as e:
        cleanup_file(output_filepath)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
