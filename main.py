import os
import uuid
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
from pydub import AudioSegment

MODELS = {
    "ryan": "/app/models/ryan.onnx",
    "amy": "/app/models/amy.onnx",
    "lessac": "/app/models/lessac.onnx",
    "alan": "/app/models/alan.onnx"
}
TEMP_DIR = "/tmp"
BGM_PATH = "/app/suspense_bgm.ogg"  # Hamara Naya Music File

app = FastAPI(title="Multi-Voice TTS with BGM Microservice", version="4.0.0")

class DialogueLine(BaseModel):
    voice: str = Field(..., description="Voice name: 'ryan', 'amy', 'lessac', or 'alan'")
    text: str = Field(..., min_length=1, description="Text to speak")

class TTSRequest(BaseModel):
    dialogues: List[DialogueLine] = Field(..., description="List of dialogues")
    add_bgm: bool = Field(default=True, description="Whether to add background music") # Naya feature!

def cleanup_files(filepaths: List[str]):
    for path in filepaths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Multi-Voice & BGM Studio is Ready!"}

@app.post("/generate-audio")
def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    final_output = os.path.join(TEMP_DIR, f"final_{session_id}.wav")
    temp_files = [] 
    
    combined_audio = AudioSegment.empty()

    try:
        print(f"🚀 Processing Script: {len(request.dialogues)} lines...")
        
        for idx, line in enumerate(request.dialogues):
            voice_key = line.voice.lower()
            if voice_key not in MODELS:
                voice_key = "ryan"
            
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
                combined_audio += AudioSegment.silent(duration=300)
            else:
                raise Exception(f"Generated empty file for voice {voice_key}")

        # 🎵 THE MAGIC: Background Music (BGM) Mixing Logic
        if request.add_bgm and os.path.exists(BGM_PATH) and len(combined_audio) > 0:
            print("🎵 Adding Background Suspense Music...")
            bgm = AudioSegment.from_file(BGM_PATH)
            
            # Music ki aawaz ko -14 dB kam karna taaki dialogues clear sunein
            bgm = bgm - 14 
            
            # BGM ko utni baar loop karna jitni lambi hamari story hai
            loop_count = (len(combined_audio) // len(bgm)) + 1
            bgm_looped = bgm * loop_count
            
            # BGM ko exact story ki timing par cut karna
            bgm_looped = bgm_looped[:len(combined_audio)]
            
            # Dialogues aur BGM ko ek sath mix kar dena!
            combined_audio = combined_audio.overlay(bgm_looped)

        combined_audio.export(final_output, format="wav")
        temp_files.append(final_output)

        background_tasks.add_task(cleanup_files, temp_files)

        return FileResponse(
            final_output, 
            media_type="audio/wav", 
            filename=f"movie_mix_{session_id[:8]}.wav"
        )

    except Exception as e:
        cleanup_files(temp_files)
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
