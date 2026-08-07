from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class VoiceOrderResponse(BaseModel):
    transcript: str
    reply_text: str
    conversation: list[ChatMessage]
