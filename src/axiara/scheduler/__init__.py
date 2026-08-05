"""Task scheduler for Axiara using APScheduler.

Implements scheduled tasks:
- Weekly upload reminder (manual trigger only)
- Optional weekly crawler refresh (confirm-gated)
- Monthly scale health report (D-SK10)
- Archive detection (D-SK11, admin-confirmed)
"""

from __future__ import annotations

from axiara.scheduler.jobs import (
    archive_detection_job,
    disable_job,
    enable_job,
    get_scheduler,
    monthly_scale_report_job,
    register_jobs,
    start_scheduler,
    stop_scheduler,
    trigger_job,
    weekly_crawler_refresh_job,
    weekly_upload_reminder_job,
)

__all__ = [
    "archive_detection_job",
    "disable_job",
    "enable_job",
    "get_scheduler",
    "monthly_scale_report_job",
    "register_jobs",
    "start_scheduler",
    "stop_scheduler",
    "trigger_job",
    "weekly_crawler_refresh_job",
    "weekly_upload_reminder_job",
]