import os
import sys
from pathlib import Path

from app.config import settings

if settings.whisper_device == "cuda":
    # ctranslate2 needs cuBLAS/cuDNN at runtime. Rather than requiring a full CUDA Toolkit
    # install, we pull them in as pip packages (nvidia-cublas-cu12, nvidia-cudnn-cu12) - but
    # Windows won't find their DLLs on PATH automatically, so register the directories explicitly.
    _venv_site_packages = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    for _dll_dir in (_venv_site_packages / "cublas" / "bin", _venv_site_packages / "cudnn" / "bin"):
        if _dll_dir.is_dir():
            os.add_dll_directory(str(_dll_dir))
            # ctranslate2's CUDA loader walks PATH directly rather than only the AddDllDirectory
            # registry - add_dll_directory alone wasn't enough in testing.
            os.environ["PATH"] = str(_dll_dir) + os.pathsep + os.environ.get("PATH", "")

from faster_whisper import WhisperModel  # noqa: E402 - must follow the DLL directory registration above


class SpeechToText:
    def __init__(self) -> None:
        self._model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        # Whisper has a single "ar" code covering MSA and all dialects (Egyptian included) - there's
        # no dialect-specific code to pass. Pinning it (instead of leaving None/auto-detect) avoids
        # misdetection on short utterances, which matters more the more colloquial the speech is.
        language = language or settings.stt_language or None
        segments, _info = self._model.transcribe(audio_path, language=language)
        return "".join(segment.text for segment in segments).strip()


speech_to_text = SpeechToText()
