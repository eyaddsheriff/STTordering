# ═══════════════════════════════════════════════
# main.py — FastAPI Application Entry Point (Updated)
# ═══════════════════════════════════════════════

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.redis import close_redis, get_redis

from app.api.routes import (
    restaurants_router, categories_router, menu_router,
    customers_router, sessions_router, orders_router,
    conversations_router, sync_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        r = await get_redis()
        await r.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
    print(f"🚀 {settings.app_name} v{settings.app_version} started")
    yield
    await close_redis()
    print("👋 Application shutdown complete")


# ─── Create App ───
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(restaurants_router, prefix=f"{settings.api_prefix}/restaurants")
app.include_router(categories_router, prefix=f"{settings.api_prefix}/categories")
app.include_router(menu_router, prefix=f"{settings.api_prefix}/menu")
app.include_router(customers_router, prefix=f"{settings.api_prefix}/customers")
app.include_router(sessions_router, prefix=f"{settings.api_prefix}/sessions")
app.include_router(orders_router, prefix=f"{settings.api_prefix}/orders")
app.include_router(conversations_router, prefix=f"{settings.api_prefix}/conversations")
app.include_router(sync_router, prefix=f"{settings.api_prefix}/sync")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.api_prefix,
    }