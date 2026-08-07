from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # TTS provider: "openai" or "piper" (local, no API key needed)
    tts_provider: str = "piper"

    # OpenAI (used for TTS when tts_provider="openai")
    openai_api_key: str = ""
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "alloy"

    # Piper (local TTS, used when tts_provider="piper")
    piper_voices_dir: str = "voices"
    piper_voice: str = "en_US-amy-medium"

    # LLM provider: "deepseek" or "ollama" (local, no API key needed)
    llm_provider: str = "ollama"

    # DeepSeek (OpenAI-compatible API, used when llm_provider="deepseek")
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Ollama (local, OpenAI-compatible API, used when llm_provider="ollama")
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    # faster-whisper (local STT)
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"


settings = Settings()
