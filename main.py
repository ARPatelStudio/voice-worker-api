import os
import uuid
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
from pydub import AudioSegment

# Models map - Ab hamare paas 4 aawazein hain!
MODELS = {
    "ryan": "/app/models/ryan.onnx",
    "amy": "/app/models/amy.onnx",
    "lessac": "/app/models/lessac.onnx",
    "alan": "/app/models/alan.onnx"
}
TEMP_DIR = "/tmp"

app = FastAPI(title="Multi-Voice TTS Microservice", version="3.1.0")

class DialogueLine(BaseModel):
    voice: str = Field(..., description="Voice name: 'ryan', 'amy', 'lessac', or 'alan'")
    text: str = Field(..., min_length=1, description="Text to speak")

class TTSRequest(BaseModel):
    dialogues: List[DialogueLine] = Field(..., description="List of dialogues")

def cleanup_files(filepaths: List[str]):
    for path in filepaths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "4-Voice Studio is Ready!"}

@app.post("/generate-audio")
def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    final_output = os.path.join(TEMP_DIR, f"final_{session_id}.wav")
    temp_files = [] 
    
    combined_audio = AudioSegment.empty()

    try:
        print(f"🚀 Processing 4-Voice Script: {len(request.dialogues)} lines...")
        
        for idx, line in enumerate(request.dialogues):
            voice_key = line.voice.lower()
            if voice_key not in MODELS:
                voice_key = "ryan" # Agar naam galat hua toh Ryan bolega
            
            model_path = MODELS[voice_key]
            temp_wav = os.path.join(TEMP_DIR, f"temp_{session_id}_{idx}.wav")
            temp_files.append(temp_wav)
            
            command = ["piper", "--model", model_path, "--output_file", temp_wav]
            process = subprocess.run(command, input=line.text.encode("utf-8"), capture_output=True)
            
            if process.returncode != 0:
                raise Exception(f"Piper Error for voice {voice_key}: {process.stderr.decode('utf-8')}")
            
            if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
                segment = AudioSegment.from_wav(temp_wav)
                combined_audio += segment
                combined_audio += AudioSegment.silent(duration=300) # Thoda aur natural pause (300ms)
            else:
                raise Exception(f"Generated empty file for voice {voice_key}")

        combined_audio.export(final_output, format="wav")
        temp_files.append(final_output)

        background_tasks.add_task(cleanup_files, temp_files)

        return FileResponse(
            final_output, 
            media_type="audio/wav", 
            filename=f"studio_mix_{session_id[:8]}.wav"
        )

    except Exception as e:
        cleanup_files(temp_files)
        raise HTTPException(status_code=500, detail=f"Multi-audio generation failed: {str(e)}")
