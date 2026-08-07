import io
import wave
from functools import cached_property
from pathlib import Path

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

    def synthesize(self, text: str) -> bytes:
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


text_to_speech = TextToSpeech()
