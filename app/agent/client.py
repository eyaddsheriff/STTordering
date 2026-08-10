from functools import lru_cache

from openai import OpenAI

from app.config import settings


@lru_cache
def get_client() -> OpenAI:
    if settings.llm_provider == "ollama":
        return OpenAI(api_key="ollama", base_url=settings.ollama_base_url)
    return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)


def get_model() -> str:
    return settings.ollama_model if settings.llm_provider == "ollama" else settings.deepseek_model
