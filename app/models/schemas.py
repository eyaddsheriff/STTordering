from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class OrderItem(BaseModel):
    name: str
    quantity: int
    notes: str
    item_id: str | None
    price: float | None


class InvalidOrderItem(BaseModel):
    name: str
    reason: str


class VoiceOrderResponse(BaseModel):
    session_id: str
    transcript: str
    reply_text: str
    conversation: list[ChatMessage]
    intent: str
    order_items: list[OrderItem]
    invalid_items: list[InvalidOrderItem]
    order_confirmed: bool
