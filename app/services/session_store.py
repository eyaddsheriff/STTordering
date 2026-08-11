"""Redis-backed per-call session memory (Phase 1 4.8 gap in CLAUDE_1.md).

Replaces the old design where the client had to resend the entire conversation transcript on
every request. Now the server holds conversation history and last-known order state under a
session_id, refreshing a TTL on each turn so idle calls expire instead of living forever.
"""

import json
import uuid

from redis.asyncio import Redis

from app.config import settings

_redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def new_session_id() -> str:
    return str(uuid.uuid4())


def _conversation_key(session_id: str) -> str:
    return f"session:{session_id}:conversation"


def _order_state_key(session_id: str) -> str:
    return f"session:{session_id}:order_state"


async def get_conversation(session_id: str) -> list[dict]:
    raw = await _redis.get(_conversation_key(session_id))
    return json.loads(raw) if raw else []


async def save_conversation(session_id: str, conversation: list[dict]) -> None:
    await _redis.set(_conversation_key(session_id), json.dumps(conversation), ex=settings.session_ttl_seconds)


async def get_order_state(session_id: str) -> dict:
    raw = await _redis.get(_order_state_key(session_id))
    return json.loads(raw) if raw else {"order_items": [], "invalid_items": [], "order_confirmed": False}


async def save_order_state(
    session_id: str, order_items: list[dict], invalid_items: list[dict], order_confirmed: bool
) -> None:
    state = {"order_items": order_items, "invalid_items": invalid_items, "order_confirmed": order_confirmed}
    await _redis.set(_order_state_key(session_id), json.dumps(state), ex=settings.session_ttl_seconds)
