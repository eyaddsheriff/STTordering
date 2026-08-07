from faster_whisper import WhisperModel

from app.config import settings


class SpeechToText:
    def __init__(self) -> None:
        self._model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        segments, _info = self._model.transcribe(audio_path, language=language)
        return "".join(segment.text for segment in segments).strip()


speech_to_text = SpeechToText()
