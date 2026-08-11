from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # TTS provider: "openai", "piper" (local, no API key needed), or "edge" (free, cloud, unofficial
    # - see the note in app/services/tts.py before relying on it in production)
    tts_provider: str = "piper"

    # OpenAI (used for TTS when tts_provider="openai")
    openai_api_key: str = ""
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"

    # Piper (local TTS, used when tts_provider="piper")
    piper_voices_dir: str = "voices"
    piper_voice: str = "en_US-amy-medium"

    # Microsoft Edge TTS (used when tts_provider="edge"). Dialect voices: ar-EG/ar-SA/ar-JO/ar-AE/...
    edge_tts_voice: str = "ar-EG-SalmaNeural"

    # LLM provider: "deepseek" or "ollama" (local, no API key needed)
    llm_provider: str = "ollama"

    # DeepSeek (OpenAI-compatible API, used when llm_provider="deepseek")
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Ollama (local, OpenAI-compatible API, used when llm_provider="ollama")
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    # faster-whisper (local STT). stt_language="ar" covers MSA + all dialects (no per-dialect code
    # exists in Whisper); leave empty for auto-detect.
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    stt_language: str = "ar"

    # Local search-layer database (Phase 2 "Sync for Search" replica — see CLAUDE_1.md)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sttordering"

    # Redis session store (Phase 1 4.8 "Order Management & Memory") - holds per-call conversation
    # history and order state server-side, keyed by session_id, so clients don't need to resend the
    # full transcript every turn.
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 1800


settings = Settings()
