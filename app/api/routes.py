import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import Response

from app.models.schemas import ChatMessage, VoiceOrderResponse
from app.services.llm import order_assistant
from app.services.stt import speech_to_text
from app.services.tts import text_to_speech

router = APIRouter(prefix="/api")


@router.post("/voice-order", response_model=VoiceOrderResponse)
async def voice_order(audio: UploadFile, conversation: str = Form("[]")) -> VoiceOrderResponse:
    history = [ChatMessage(**m) for m in json.loads(conversation)]

    with tempfile.NamedTemporaryFile(suffix=Path(audio.filename or "audio.wav").suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    transcript = speech_to_text.transcribe(tmp_path)

    history.append(ChatMessage(role="user", content=transcript))
    reply_text = order_assistant.reply([m.model_dump() for m in history])
    history.append(ChatMessage(role="assistant", content=reply_text))

    return VoiceOrderResponse(transcript=transcript, reply_text=reply_text, conversation=history)


@router.post("/speak")
async def speak(text: str = Form(...)) -> Response:
    audio_bytes = text_to_speech.synthesize(text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
