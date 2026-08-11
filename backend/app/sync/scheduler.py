# ═══════════════════════════════════════════════
# sync/scheduler.py — APScheduler Config (Phase 6)
# ═══════════════════════════════════════════════

from apscheduler.schedulers.asyncio import AsyncIOScheduler

_scheduler: AsyncIOScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()
        print("🕐 Scheduler started (Phase 6 placeholder)")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        print("🕐 Scheduler stopped")