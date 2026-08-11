# ═══════════════════════════════════════════════
# api/routes/__init__.py — API Routes Package
# ═══════════════════════════════════════════════

from fastapi import APIRouter

from app.api.routes.restaurants import router as restaurants_router
from app.api.routes.categories import router as categories_router
from app.api.routes.menu import router as menu_router
from app.api.routes.customers import router as customers_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.orders import router as orders_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.sync import router as sync_router

__all__ = [
    "restaurants_router",
    "categories_router",
    "menu_router",
    "customers_router",
    "sessions_router",
    "orders_router",
    "conversations_router",
    "sync_router",
]