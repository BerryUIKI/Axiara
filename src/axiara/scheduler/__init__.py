"""Task scheduler (APScheduler) — scaffold. On-demand execution."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler() -> BackgroundScheduler:
    """Create the background scheduler (jobs added later)."""
    return BackgroundScheduler()
