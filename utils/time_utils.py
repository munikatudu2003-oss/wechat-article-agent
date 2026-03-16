from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_epoch_millis() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)
