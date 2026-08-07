from functools import cached_property

from openai import OpenAI

from app.config import settings

SYSTEM_PROMPT = (
    "You are a voice ordering assistant for a restaurant. "
    "Help the customer build their order, ask clarifying questions about "
    "size/options, and confirm the final order back to them. Keep replies short "
    "and natural, since they will be read aloud."
)


class OrderAssistant:
    @cached_property
    def _client(self) -> OpenAI:
        if settings.llm_provider == "ollama":
            return OpenAI(api_key="ollama", base_url=settings.ollama_base_url)
        return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    @property
    def _model(self) -> str:
        return settings.ollama_model if settings.llm_provider == "ollama" else settings.deepseek_model

    def reply(self, conversation: list[dict[str, str]]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *conversation]
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content or ""


order_assistant = OrderAssistant()
