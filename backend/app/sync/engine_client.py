# ═══════════════════════════════════════════════
# sync/engine_client.py — Restaurant Engine Client (Phase 6)
# ═══════════════════════════════════════════════

import httpx

from app.core.config import get_settings

settings = get_settings()


class EngineClient:
    def __init__(self):
        self.base_url = settings.restaurant_engine_base_url
        self.api_key = settings.restaurant_engine_api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    async def get_menu(self, restaurant_external_id: str):
        pass

    async def check_availability(self, item_external_id: str):
        pass

    async def create_order(self, order_data: dict):
        pass