# ═══════════════════════════════════════════════
# utils/helpers.py — General Utilities
# ═══════════════════════════════════════════════

from datetime import datetime


def format_datetime(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()