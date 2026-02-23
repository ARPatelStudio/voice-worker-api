import os
import uuid
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Define constants
MODEL_PATH = "/app/models/voice.onnx"
TEMP_DIR = "/tmp"

# Initialize FastAPI application
app = FastAPI(title="Piper TTS Microservice", version="2.0.0")

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize.")

def cleanup_file(filepath: str):
    """Deletes the audio file after it's successfully sent."""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🗑️ Cleanup done: {filepath}")
        except:
            pass

@app.get("/health")
def health_check():
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=503, detail="Model missing.")
    return {"status": "ok", "message": "Piper CLI System Ready!"}

@app.post("/generate-audio")
def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=500, detail="TTS Model file missing.")
    
    session_id = str(uuid.uuid4())
    output_filepath = os.path.join(TEMP_DIR, f"voiceover_{session_id}.wav")

    try:
        print(f"🚀 Generating CLI Audio for: {request.text[:40]}...")
        
        # BRAHMASTRA: Calling Piper directly via system terminal
        command = [
            "piper",
            "--model", MODEL_PATH,
            "--output_file", output_filepath
        ]
        
        process = subprocess.run(
            command,
            input=request.text.encode("utf-8"),
            capture_output=True
        )
        
        if process.returncode != 0:
            error_msg = process.stderr.decode("utf-8")
            raise Exception(f"Piper System Error: {error_msg}")
            
        if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) == 0:
            raise Exception("Piper generated an empty 0 Byte file.")

        background_tasks.add_task(cleanup_file, output_filepath)

        return FileResponse(
            output_filepath, 
            media_type="audio/wav", 
            filename=f"voiceover_{session_id[:8]}.wav"
        )

    except Exception as e:
        cleanup_file(output_filepath)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
