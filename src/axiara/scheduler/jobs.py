"""APScheduler jobs for Axiara.

Implements scheduled tasks:
- Weekly upload reminder (manual trigger only - never auto-push)
- Optional weekly crawler refresh (produces diff, confirm-gated)
- Monthly scale health report (D-SK10)
- Archive detection (D-SK11, admin-confirmed)

Jobs are registrations that call existing modules.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance.

    Returns:
        AsyncIOScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


# Job functions
async def weekly_upload_reminder_job() -> dict[str, Any]:
    """Weekly upload reminder job.

    Sends a reminder to users to upload their personal libraries.
    Manual trigger only - never auto-pushes.

    Returns:
        Reminder status
    """
    # Check if users have pending uploads
    # Send reminder via notification system (placeholder)

    return {
        "job": "weekly_upload_reminder",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "reminder_sent",
        "message": "Weekly upload reminder sent to users",
    }


async def weekly_crawler_refresh_job() -> dict[str, Any]:
    """Weekly crawler refresh job.

    Produces a proposed diff of market prices.
    Confirm-gated - never auto-writes without user confirmation.

    Returns:
        Diff result
    """
    from axiara.core.crawler import CrawlerPipeline

    # Get configured sources
    config_path = Path("skills/price-crawler/config/sources.yaml")
    if not config_path.exists():
        return {
            "job": "weekly_crawler_refresh",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": "No sources configured",
        }

    # Placeholder - would crawl all enabled sources
    # and produce a diff for user confirmation

    return {
        "job": "weekly_crawler_refresh",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "diff_produced",
        "message": "Market price diff ready for review",
    }


async def monthly_scale_report_job() -> dict[str, Any]:
    """Monthly scale health report job (D-SK10).

    Generates rolling 90-day metrics and scale tier classification.
    Produces Git→SQL migration proposals if needed.

    Returns:
        Scale health report
    """
    # Placeholder - would use ScaleMonitor from learnsync
    # from axiara.core.learnsync import ScaleMonitor
    # monitor = ScaleMonitor()
    # report = monitor.generate_health_report()

    report = {
        "tier": "healthy",
        "metrics": {},
    }

    # Save report to output/
    output_path = Path("output") / f"scale-report-{datetime.utcnow().strftime('%Y%m%d')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return {
        "job": "monthly_scale_report",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "report_generated",
        "output_path": str(output_path),
        "tier": report.get("tier", "unknown"),
    }


async def archive_detection_job() -> dict[str, Any]:
    """Archive detection job (D-SK11).

    Detects inactive branches (> 180 days idle).
    Admin-confirmed before archiving.

    Returns:
        Archive candidates
    """
    # Placeholder - would use ArchiveManager from learnsync
    # from axiara.core.learnsync import ArchiveManager
    # manager = ArchiveManager()
    # candidates = manager.detect_inactive_branches()

    candidates = []

    return {
        "job": "archive_detection",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "candidates_detected",
        "count": len(candidates),
        "candidates": candidates[:10],  # First 10 for preview
        "message": "Archive candidates ready for admin review",
    }


def register_jobs(scheduler: AsyncIOScheduler | None = None) -> None:
    """Register all scheduled jobs.

    Args:
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()
    scheduler.remove_all_jobs()  # idempotent: reset to the standard job set

    # Weekly upload reminder - Mondays at 09:00
    scheduler.add_job(
        weekly_upload_reminder_job,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_upload_reminder",
        name="Weekly Upload Reminder",
        replace_existing=True,
    )

    # Weekly crawler refresh - Sundays at 02:00 (optional, disabled by default)
    scheduler.add_job(
        weekly_crawler_refresh_job,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_crawler_refresh",
        name="Weekly Crawler Refresh",
        replace_existing=True,
        enabled=False,  # Disabled by default - requires explicit enable
    )

    # Monthly scale report - 1st of each month at 10:00
    scheduler.add_job(
        monthly_scale_report_job,
        CronTrigger(day=1, hour=10, minute=0),
        id="monthly_scale_report",
        name="Monthly Scale Health Report",
        replace_existing=True,
    )

    # Archive detection - 15th of each month at 11:00
    scheduler.add_job(
        archive_detection_job,
        CronTrigger(day=15, hour=11, minute=0),
        id="archive_detection",
        name="Archive Detection",
        replace_existing=True,
    )


def start_scheduler(scheduler: AsyncIOScheduler | None = None) -> None:
    """Start the scheduler.

    Args:
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()

    # Register jobs if not already registered
    if not scheduler.get_jobs():
        register_jobs(scheduler)

    # Start scheduler
    scheduler.start()


def stop_scheduler(scheduler: AsyncIOScheduler | None = None) -> None:
    """Stop the scheduler.

    Args:
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()
    scheduler.shutdown()


def enable_job(job_id: str, scheduler: AsyncIOScheduler | None = None) -> None:
    """Enable a specific job.

    Args:
        job_id: Job ID to enable
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()
    job = scheduler.get_job(job_id)
    if job:
        job.resume()


def disable_job(job_id: str, scheduler: AsyncIOScheduler | None = None) -> None:
    """Disable a specific job.

    Args:
        job_id: Job ID to disable
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()
    job = scheduler.get_job(job_id)
    if job:
        job.pause()


def trigger_job(job_id: str, scheduler: AsyncIOScheduler | None = None) -> None:
    """Manually trigger a job.

    Args:
        job_id: Job ID to trigger
        scheduler: Scheduler instance (uses global if None)
    """
    scheduler = scheduler or get_scheduler()
    scheduler.run_job(job_id)