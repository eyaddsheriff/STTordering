import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import Response

from app.agent import order_agent
from app.models.schemas import ChatMessage, VoiceOrderResponse
from app.services import session_store
from app.services.stt import speech_to_text
from app.services.tts import text_to_speech

router = APIRouter(prefix="/api")


@router.post("/voice-order", response_model=VoiceOrderResponse)
async def voice_order(audio: UploadFile, session_id: str | None = Form(None)) -> VoiceOrderResponse:
    session_id = session_id or session_store.new_session_id()
    history = [ChatMessage(**m) for m in await session_store.get_conversation(session_id)]

    with tempfile.NamedTemporaryFile(suffix=Path(audio.filename or "audio.wav").suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    transcript = speech_to_text.transcribe(tmp_path)
    history.append(ChatMessage(role="user", content=transcript))

    result = await order_agent.ainvoke({"conversation": [m.model_dump() for m in history]})
    history.append(ChatMessage(role="assistant", content=result["reply_text"]))

    await session_store.save_conversation(session_id, [m.model_dump() for m in history])
    await session_store.save_order_state(
        session_id,
        result.get("order_items", []),
        result.get("invalid_items", []),
        result.get("order_confirmed", False),
    )

    return VoiceOrderResponse(
        session_id=session_id,
        transcript=transcript,
        reply_text=result["reply_text"],
        conversation=history,
        intent=result["intent"],
        order_items=result.get("order_items", []),
        invalid_items=result.get("invalid_items", []),
        order_confirmed=result.get("order_confirmed", False),
    )


@router.post("/speak")
async def speak(text: str = Form(...)) -> Response:
    audio_bytes = await text_to_speech.synthesize(text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
