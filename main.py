from fastapi.responses import Response
import io

@app.post("/generate-audio")
async def generate_audio(request: TTSRequest):
    voice_model = ml_models.get("voice")

    if not voice_model:
        raise HTTPException(status_code=500, detail="TTS Model is not initialized.")

    try:
        # Memory buffer create karo
        audio_buffer = io.BytesIO()

        # IMPORTANT: synthesize return value ko capture karo
        audio_bytes = voice_model.synthesize(request.text)

        # Write manually
        audio_buffer.write(audio_bytes)
        audio_buffer.seek(0)

        print(f"Generated audio size: {len(audio_bytes)} bytes")

        return Response(
            content=audio_buffer.read(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=voice.wav"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
