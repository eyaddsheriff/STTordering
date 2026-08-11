import io
import wave
from functools import cached_property
from pathlib import Path

import edge_tts
from openai import OpenAI
from piper import PiperVoice

from app.config import settings


class TextToSpeech:
    @cached_property
    def _openai_client(self) -> OpenAI:
        return OpenAI(api_key=settings.openai_api_key)

    @cached_property
    def _piper_voice(self) -> PiperVoice:
        model_path = Path(settings.piper_voices_dir) / f"{settings.piper_voice}.onnx"
        return PiperVoice.load(model_path)

    async def synthesize(self, text: str) -> bytes:
        if settings.tts_provider == "edge":
            return await self._synthesize_edge(text)
        if settings.tts_provider == "piper":
            return self._synthesize_piper(text)
        return self._synthesize_openai(text)

    def _synthesize_openai(self, text: str) -> bytes:
        response = self._openai_client.audio.speech.create(
            model=settings.tts_model,
            voice=settings.tts_voice,
            input=text,
        )
        return response.read()

    def _synthesize_piper(self, text: str) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            self._piper_voice.synthesize_wav(text, wav_file)
        return buffer.getvalue()

    async def _synthesize_edge(self, text: str) -> bytes:
        # Free, genuinely native-accent Arabic dialect voices (ar-EG, ar-SA, ar-JO, ...), but calls
        # Microsoft's cloud via an unofficial/reverse-engineered integration (piggybacks on Edge
        # browser's read-aloud feature, not a published API) - fine for dev/testing, revisit before
        # relying on it in production (swap to OpenAI TTS or Azure's official Speech API).
        communicate = edge_tts.Communicate(text, voice=settings.edge_tts_voice)
        chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.extend(chunk["data"])
        return bytes(chunks)


text_to_speech = TextToSpeech()
