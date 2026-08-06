"""Dynamic scale monitoring for learn sync (D-SK10).

Implements floating monitoring:
- Rolling 90-day metrics
- Active contributors count
- Weekly upload volume
- Review backlog
- Branch/file sprawl
- Friction events

Provides tier classification and migration recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class ScaleTier(StrEnum):
    """Scale health tiers."""
    
    HEALTHY = "healthy"  # 🟢
    WATCH = "watch"  # 🟡
    UPGRADE_ADVISED = "upgrade_advised"  # 🟠
    MUST_MIGRATE = "must_migrate"  # 🔴


@dataclass
class ScaleMetrics:
    """Metrics for scale monitoring (rolling 90-day)."""
    
    active_contributors: int = 0
    weekly_upload_volume: float = 0.0
    avg_bundle_size: float = 0.0
    review_backlog_size: int = 0
    review_backlog_days: float = 0.0
    user_branch_count: int = 0
    inbox_file_count: int = 0
    friction_events: int = 0
    
    # Trends
    contributors_trend: float = 0.0  # % change
    upload_volume_trend: float = 0.0  # % change
    backlog_trend: float = 0.0  # % change
    
    calculated_at: datetime | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "active_contributors": self.active_contributors,
            "weekly_upload_volume": self.weekly_upload_volume,
            "avg_bundle_size": self.avg_bundle_size,
            "review_backlog_size": self.review_backlog_size,
            "review_backlog_days": self.review_backlog_days,
            "user_branch_count": self.user_branch_count,
            "inbox_file_count": self.inbox_file_count,
            "friction_events": self.friction_events,
            "contributors_trend": self.contributors_trend,
            "upload_volume_trend": self.upload_volume_trend,
            "backlog_trend": self.backlog_trend,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }


@dataclass
class ScaleReport:
    """A scale health report."""
    
    tier: ScaleTier
    metrics: ScaleMetrics
    violations: list[str]
    recommendations: list[str]
    migration_proposal: str | None = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tier": self.tier.value,
            "metrics": self.metrics.to_dict(),
            "violations": self.violations,
            "recommendations": self.recommendations,
            "migration_proposal": self.migration_proposal,
            "generated_at": self.generated_at.isoformat(),
        }


class ScaleMonitor:
    """Monitors scale metrics and provides tier classification.
    
    Per learn-sync.md §10.1:
    - Rolling 90-day window
    - Four tiers: 🟢 healthy, 🟡 watch, 🟠 upgrade advised, 🔴 must migrate
    - Dynamic threshold checking
    - Migration recommendations
    """
    
    # Tier thresholds
    TIERS = {
        ScaleTier.HEALTHY: {
            "max_contributors": 10,
            "max_backlog_days": 7,
        },
        ScaleTier.WATCH: {
            "max_contributors": 30,
            "max_backlog_days": 14,
        },
        ScaleTier.UPGRADE_ADVISED: {
            "max_contributors": 100,
            "max_backlog_days": 30,
        },
        ScaleTier.MUST_MIGRATE: {
            "max_contributors": float("inf"),
            "max_backlog_days": float("inf"),
        },
    }
    
    def __init__(
        self,
        store_dir: Path | None = None,
        window_days: int = 90,
    ) -> None:
        """Initialize scale monitor.
        
        Args:
            store_dir: Store directory (default: .data/store/)
            window_days: Rolling window in days (default: 90)
        """
        self.store_dir = store_dir or Path(".data/store")
        self.window_days = window_days
        self.window_start = datetime.now(timezone.utc) - timedelta(days=window_days)
    
    def calculate_metrics(self) -> ScaleMetrics:
        """Calculate current metrics.
        
        Returns:
            ScaleMetrics instance
        """
        metrics = ScaleMetrics(calculated_at=datetime.now(timezone.utc))
        
        # Count active contributors (users who uploaded in window)
        contributors = self._count_active_contributors()
        metrics.active_contributors = len(contributors)
        
        # Calculate upload volume
        uploads = self._get_uploads_in_window()
        metrics.weekly_upload_volume = len(uploads) / (self.window_days / 7)
        
        # Calculate average bundle size
        if uploads:
            total_rules = sum(u.get("rule_count", 0) for u in uploads)
            metrics.avg_bundle_size = total_rules / len(uploads)
        
        # Count review backlog
        backlog = self._count_review_backlog()
        metrics.review_backlog_size = backlog.get("size", 0)
        metrics.review_backlog_days = backlog.get("oldest_days", 0.0)
        
        # Count branches and files
        metrics.user_branch_count = self._count_user_branches()
        metrics.inbox_file_count = self._count_inbox_files()
        
        # Count friction events
        metrics.friction_events = self._count_friction_events()
        
        # Calculate trends
        metrics.contributors_trend = self._calculate_trend("contributors")
        metrics.upload_volume_trend = self._calculate_trend("upload_volume")
        metrics.backlog_trend = self._calculate_trend("backlog")
        
        return metrics
    
    def _count_active_contributors(self) -> set[str]:
        """Count users who uploaded in the window.
        
        Returns:
            Set of user IDs
        """
        contributors: set[str] = set()
        inbox_dir = self.store_dir / "learn_inbox"
        
        if not inbox_dir.exists():
            return contributors
        
        for user_dir in inbox_dir.iterdir():
            if user_dir.is_dir() and user_dir.name.startswith("AX-"):
                # Check for uploads in window
                for date_dir in user_dir.iterdir():
                    if date_dir.is_dir():
                        try:
                            upload_date = datetime.strptime(date_dir.name, "%Y%m%d").replace(tzinfo=timezone.utc)
                            if upload_date >= self.window_start:
                                contributors.add(user_dir.name)
                                break
                        except ValueError:
                            continue
        
        return contributors
    
    def _get_uploads_in_window(self) -> list[dict[str, Any]]:
        """Get uploads within the window.
        
        Returns:
            List of upload info dicts
        """
        uploads: list[dict[str, Any]] = []
        inbox_dir = self.store_dir / "learn_inbox"
        
        if not inbox_dir.exists():
            return uploads
        
        for user_dir in inbox_dir.iterdir():
            if user_dir.is_dir() and user_dir.name.startswith("AX-"):
                for date_dir in user_dir.iterdir():
                    if date_dir.is_dir():
                        try:
                            upload_date = datetime.strptime(date_dir.name, "%Y%m%d").replace(tzinfo=timezone.utc)
                            if upload_date >= self.window_start:
                                bundle_file = date_dir / "bundle.yaml"
                                if bundle_file.exists():
                                    # Load bundle metadata
                                    try:
                                        content = bundle_file.read_text(encoding="utf-8")
                                        data = yaml.safe_load(content) or {}
                                        meta = data.get("metadata", {})
                                        uploads.append({
                                            "user_id": user_dir.name,
                                            "date": date_dir.name,
                                            "rule_count": meta.get("rule_count", 0),
                                        })
                                    except Exception:
                                        uploads.append({
                                            "user_id": user_dir.name,
                                            "date": date_dir.name,
                                            "rule_count": 0,
                                        })
                        except ValueError:
                            continue
        
        return uploads
    
    def _count_review_backlog(self) -> dict[str, Any]:
        """Count pending reviews and oldest pending age.
        
        Returns:
            Dict with size and oldest_days
        """
        backlog_size = 0
        oldest_date: datetime | None = None
        
        reviews_dir = self.store_dir / "learn_inbox" / "_reviews"
        
        if reviews_dir.exists():
            for review_dir in reviews_dir.iterdir():
                if review_dir.is_dir():
                    try:
                        review_date = datetime.strptime(review_dir.name, "%Y%m%d")
                        
                        proposals_file = review_dir / "proposals.yaml"
                        if proposals_file.exists():
                            try:
                                content = proposals_file.read_text(encoding="utf-8")
                                data = yaml.safe_load(content) or {}
                                
                                if data.get("status") == "pending":
                                    backlog_size += 1
                                    if oldest_date is None or review_date < oldest_date:
                                        oldest_date = review_date
                            except Exception:
                                pass
                    except ValueError:
                        continue
        
        oldest_days = 0.0
        if oldest_date:
            oldest_days = (datetime.now(timezone.utc) - oldest_date.replace(tzinfo=timezone.utc)).total_seconds() / 86400
        
        return {
            "size": backlog_size,
            "oldest_days": oldest_days,
        }
    
    def _count_user_branches(self) -> int:
        """Count user/* branches in repo.
        
        Returns:
            Number of user branches
        """
        import subprocess
        
        try:
            result = subprocess.run(
                ["git", "branch", "--list", "user/*"],
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            
            branches = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return len(branches)
        
        except Exception:
            # Fallback: count directories
            inbox_dir = self.store_dir / "learn_inbox"
            if inbox_dir.exists():
                return len([d for d in inbox_dir.iterdir() if d.is_dir() and d.name.startswith("AX-")])
            return 0
    
    def _count_inbox_files(self) -> int:
        """Count files in learn_inbox.
        
        Returns:
            Number of files
        """
        inbox_dir = self.store_dir / "learn_inbox"
        
        if not inbox_dir.exists():
            return 0
        
        count = 0
        for f in inbox_dir.rglob("*"):
            if f.is_file():
                count += 1
        
        return count
    
    def _count_friction_events(self) -> int:
        """Count friction events (stale markers, conflicts, tombstones).
        
        Returns:
            Number of friction events
        """
        count = 0
        inbox_dir = self.store_dir / "learn_inbox"
        
        if not inbox_dir.exists():
            return count
        
        # Count stale markers
        for stale_marker in inbox_dir.rglob(".stale"):
            count += 1
        
        # Count tombstone markers (if implemented)
        # ...
        
        return count
    
    def _calculate_trend(self, metric_name: str) -> float:
        """Calculate trend for a metric.
        
        Compares current window to previous window.
        
        Args:
            metric_name: Metric to calculate trend for
            
        Returns:
            Percentage change (positive = increasing)
        """
        # Simplified: would need historical data storage for real trend calculation
        # For now, return 0 (no trend data)
        return 0.0
    
    def classify_tier(self, metrics: ScaleMetrics) -> tuple[ScaleTier, list[str]]:
        """Classify metrics into a tier.
        
        Args:
            metrics: Calculated metrics
            
        Returns:
            Tuple of (tier, list of violated conditions)
        """
        violations: list[str] = []
        
        # Check MUST_MIGRATE conditions
        if metrics.active_contributors > 100:
            violations.append(f"Active contributors ({metrics.active_contributors}) > 100")
        if metrics.review_backlog_days > 30:
            violations.append(f"Review backlog ({metrics.review_backlog_days:.1f} days) > 30 days")
        
        if violations:
            return ScaleTier.MUST_MIGRATE, violations
        
        # Check UPGRADE_ADVISED conditions
        if metrics.active_contributors > 30:
            violations.append(f"Active contributors ({metrics.active_contributors}) > 30")
        if metrics.review_backlog_days > 14:
            violations.append(f"Review backlog ({metrics.review_backlog_days:.1f} days) > 14 days")
        
        # Check for upward trends with sprawl
        if metrics.contributors_trend > 0.1 and metrics.user_branch_count > 20:
            violations.append(f"Contributors trending up with {metrics.user_branch_count} branches")
        
        if violations:
            return ScaleTier.UPGRADE_ADVISED, violations
        
        # Check WATCH conditions
        violations = []
        
        if metrics.active_contributors > 10:
            violations.append(f"Active contributors ({metrics.active_contributors}) > 10")
        if metrics.review_backlog_days > 7:
            violations.append(f"Review backlog ({metrics.review_backlog_days:.1f} days) > 7 days")
        if metrics.upload_volume_trend > 0.2:
            violations.append("Upload volume trending up")
        
        if violations:
            return ScaleTier.WATCH, violations
        
        # Otherwise HEALTHY
        return ScaleTier.HEALTHY, []
    
    def generate_recommendations(
        self,
        tier: ScaleTier,
        violations: list[str],
    ) -> list[str]:
        """Generate recommendations based on tier.
        
        Args:
            tier: Current tier
            violations: List of violations
            
        Returns:
            List of recommendations
        """
        recommendations: list[str] = []
        
        if tier == ScaleTier.HEALTHY:
            recommendations.append("System operating normally. Keep Git strategy A (per-user branches).")
        
        elif tier == ScaleTier.WATCH:
            recommendations.append("Consider tuning review process:")
            recommendations.append("  - Batch reviews to reduce frequency")
            recommendations.append("  - Set up rotating admin schedule")
            recommendations.append("Optionally consider strategy B (single upload branch) for simpler management.")
        
        elif tier == ScaleTier.UPGRADE_ADVISED:
            recommendations.append("Scale approaching Git limits. Plan SQL migration:")
            recommendations.append("  - Export learn_shared rules")
            recommendations.append("  - Set up SQL tables (learn_rules, learn_staging, etc.)")
            recommendations.append("  - Migrate audit history")
            recommendations.append("  - Flip config to sync_mode: sql")
            recommendations.append("Consider dual-write period for safe transition.")
        
        elif tier == ScaleTier.MUST_MIGRATE:
            recommendations.append("CRITICAL: Migrate to SQL immediately:")
            recommendations.append("  - Current scale exceeds Git capacity")
            recommendations.append("  - Risk of merge conflicts and review bottlenecks")
            recommendations.append("  - SQL provides concurrent uploads, transactional applies, indexed queries")
        
        return recommendations
    
    def generate_report(self) -> ScaleReport:
        """Generate a full scale health report.
        
        Returns:
            ScaleReport instance
        """
        metrics = self.calculate_metrics()
        tier, violations = self.classify_tier(metrics)
        recommendations = self.generate_recommendations(tier, violations)
        
        migration_proposal = None
        if tier in (ScaleTier.UPGRADE_ADVISED, ScaleTier.MUST_MIGRATE):
            migration_proposal = self._propose_migration(tier, metrics)
        
        return ScaleReport(
            tier=tier,
            metrics=metrics,
            violations=violations,
            recommendations=recommendations,
            migration_proposal=migration_proposal,
        )
    
    def _propose_migration(
        self,
        tier: ScaleTier,
        metrics: ScaleMetrics,
    ) -> str:
        """Propose migration steps.
        
        Args:
            tier: Current tier
            metrics: Current metrics
            
        Returns:
            Migration proposal string
        """
        if tier == ScaleTier.UPGRADE_ADVISED:
            return f"""
Git → SQL Migration Proposal

Current metrics:
- Active contributors: {metrics.active_contributors}
- Review backlog: {metrics.review_backlog_days:.1f} days
- User branches: {metrics.user_branch_count}

Migration steps:
1. Set up SQL server (MySQL/MariaDB/PostgreSQL)
2. Create tables: learn_rules, learn_staging, learn_reviews, learn_audit
3. Export learn_shared/ rules to learn_rules table
4. Update config: sync_mode=sql, backend=mysql|mariadb|postgresql
5. Test with dual-write period (optional)
6. Cut over to SQL-only mode

Estimated downtime: 1-2 hours for data migration
Risk level: Medium (recommend dual-write overlap)
"""
        
        else:  # MUST_MIGRATE
            return f"""
CRITICAL: Immediate SQL Migration Required

Current metrics:
- Active contributors: {metrics.active_contributors}
- Review backlog: {metrics.review_backlog_days:.1f} days
- User branches: {metrics.user_branch_count}

The system has exceeded Git capacity. Immediate action required:
1. Stop new uploads temporarily
2. Set up SQL server immediately
3. Export all learn_shared data
4. Migrate to SQL within 24-48 hours
5. Resume uploads via learn_staging table

Risk level: HIGH - continued Git usage risks data integrity
"""
    
    def save_report(self, report: ScaleReport, output_dir: Path) -> Path:
        """Save report to file.
        
        Args:
            report: Scale report
            output_dir: Output directory
            
        Returns:
            Path to saved report
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"scale-health-{report.generated_at.strftime('%Y%m%d-%H%M%S')}.yaml"
        filepath = output_dir / filename
        
        content = yaml.dump(
            report.to_dict(),
            default_flow_style=False,
            sort_keys=False,
        )
        
        filepath.write_text(content, encoding="utf-8")
        
        return filepath