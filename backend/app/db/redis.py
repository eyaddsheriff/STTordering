# ═══════════════════════════════════════════════
# db/redis.py — Redis Async Connection
# ═══════════════════════════════════════════════

import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()

# ─── Redis Client ───
# Singleton pattern — created once, reused everywhere
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis async client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,  # Auto-decode bytes → str
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection — call on shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


# ─── Helper Functions ───

async def set_session_state(session_id: str, data: dict, expire: int = 3600) -> None:
    """Store temporary session state in Redis (expires in 1 hour by default)."""
    r = await get_redis()
    await r.hset(f"session:{session_id}", mapping=data)
    await r.expire(f"session:{session_id}", expire)


async def get_session_state(session_id: str) -> dict | None:
    """Retrieve session state from Redis."""
    r = await get_redis()
    data = await r.hgetall(f"session:{session_id}")
    return data if data else None


async def delete_session_state(session_id: str) -> None:
    """Delete session state from Redis."""
    r = await get_redis()
    await r.delete(f"session:{session_id}")
