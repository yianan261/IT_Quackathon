from fastapi import APIRouter, UploadFile, File, Depends
from app.context import get_service_context

router = APIRouter()

@router.post("/speech-to-text")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    services: dict = Depends(get_service_context),
):
    voice_service = services["voice_service"]
    result = await voice_service.speech_to_text(audio_file)
    return {"text": result}


@router.post("/text-to-speech")
async def text_to_speech(
    text: str,
    services: dict = Depends(get_service_context),
):
    voice_service = services["voice_service"]
    audio_data = await voice_service.text_to_speech(text)
    return {
        "audio": audio_data
    }
