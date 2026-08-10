from typing import TypedDict


class OrderItem(TypedDict):
    name: str
    quantity: int
    notes: str
    item_id: str | None
    price: float | None


class InvalidOrderItem(TypedDict):
    name: str
    reason: str


class AgentState(TypedDict):
    conversation: list[dict[str, str]]
    intent: str
    order_items: list[OrderItem]
    invalid_items: list[InvalidOrderItem]
    reply_text: str
    order_confirmed: bool
