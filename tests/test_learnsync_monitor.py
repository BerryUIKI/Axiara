"""Tests for scale monitoring (learn sync).

Tests for:
- Metrics calculation
- Tier classification
- Report generation
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from axiara.core.learnsync.monitor import (
    ScaleMetrics,
    ScaleMonitor,
    ScaleReport,
    ScaleTier,
)


class TestScaleMonitor:
    """Tests for ScaleMonitor."""
    
    def test_calculate_metrics_empty(self) -> None:
        """Test calculating metrics with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            metrics = monitor.calculate_metrics()
            
            assert metrics.active_contributors == 0
            assert metrics.user_branch_count == 0
            assert metrics.inbox_file_count == 0
    
    def test_calculate_metrics_with_uploads(self) -> None:
        """Test calculating metrics with uploads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            # Create bundle files for active users
            for user_id in ["AX-0001-abcd", "AX-0002-efgh"]:
                inbox_dir = store_dir / "learn_inbox" / user_id / datetime.now(timezone.utc).strftime("%Y%m%d")
                inbox_dir.mkdir(parents=True)
                
                bundle_data = {
                    "metadata": {
                        "user_id": user_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "rule_count": 5,
                    },
                    "rules": [],
                }
                
                bundle_file = inbox_dir / "bundle.yaml"
                bundle_file.write_text(yaml.dump(bundle_data))
            
            monitor = ScaleMonitor(store_dir=store_dir)
            metrics = monitor.calculate_metrics()
            
            assert metrics.active_contributors == 2
            assert metrics.weekly_upload_volume > 0
    
    def test_classify_tier_healthy(self) -> None:
        """Test classifying healthy tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            metrics = ScaleMetrics(
                active_contributors=5,
                review_backlog_days=3.0,
            )
            
            tier, violations = monitor.classify_tier(metrics)
            
            assert tier == ScaleTier.HEALTHY
            assert len(violations) == 0
    
    def test_classify_tier_watch(self) -> None:
        """Test classifying watch tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            metrics = ScaleMetrics(
                active_contributors=15,
                review_backlog_days=5.0,
            )
            
            tier, violations = monitor.classify_tier(metrics)
            
            assert tier == ScaleTier.WATCH
            assert len(violations) > 0
    
    def test_classify_tier_upgrade_advised(self) -> None:
        """Test classifying upgrade advised tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            metrics = ScaleMetrics(
                active_contributors=35,
                review_backlog_days=10.0,
            )
            
            tier, violations = monitor.classify_tier(metrics)
            
            assert tier == ScaleTier.UPGRADE_ADVISED
            assert len(violations) > 0
    
    def test_classify_tier_must_migrate(self) -> None:
        """Test classifying must migrate tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            metrics = ScaleMetrics(
                active_contributors=150,
                review_backlog_days=5.0,
            )
            
            tier, violations = monitor.classify_tier(metrics)
            
            assert tier == ScaleTier.MUST_MIGRATE
            assert len(violations) > 0
    
    def test_classify_tier_must_migrate_backlog(self) -> None:
        """Test must migrate tier based on backlog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            metrics = ScaleMetrics(
                active_contributors=10,
                review_backlog_days=45.0,  # Over 30 days
            )
            
            tier, violations = monitor.classify_tier(metrics)
            
            assert tier == ScaleTier.MUST_MIGRATE
    
    def test_generate_recommendations_healthy(self) -> None:
        """Test generating recommendations for healthy tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            recommendations = monitor.generate_recommendations(
                ScaleTier.HEALTHY,
                [],
            )
            
            assert len(recommendations) > 0
            assert any("Keep Git strategy" in r for r in recommendations)
    
    def test_generate_recommendations_must_migrate(self) -> None:
        """Test generating recommendations for must migrate tier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            recommendations = monitor.generate_recommendations(
                ScaleTier.MUST_MIGRATE,
                ["Active contributors (150) > 100"],
            )
            
            assert len(recommendations) > 0
            assert any("CRITICAL" in r or "immediate" in r.lower() for r in recommendations)
    
    def test_generate_report(self) -> None:
        """Test generating full report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            report = monitor.generate_report()
            
            assert report.tier in ScaleTier
            assert isinstance(report.metrics, ScaleMetrics)
            assert isinstance(report.recommendations, list)
    
    def test_save_report(self) -> None:
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            output_dir = Path(tmpdir) / "output"
            
            monitor = ScaleMonitor(store_dir=store_dir)
            
            report = monitor.generate_report()
            report_path = monitor.save_report(report, output_dir)
            
            assert report_path.exists()
            assert "scale-health" in report_path.name
            
            # Verify content
            content = report_path.read_text()
            data = yaml.safe_load(content)
            
            assert "tier" in data
            assert "metrics" in data


class TestScaleMetrics:
    """Tests for ScaleMetrics."""
    
    def test_to_dict(self) -> None:
        """Test converting metrics to dict."""
        metrics = ScaleMetrics(
            active_contributors=10,
            weekly_upload_volume=5.5,
            user_branch_count=8,
            calculated_at=datetime(2026, 8, 5, 12, 0, 0),
        )
        
        data = metrics.to_dict()
        
        assert data["active_contributors"] == 10
        assert data["weekly_upload_volume"] == 5.5
        assert "calculated_at" in data


class TestScaleReport:
    """Tests for ScaleReport."""
    
    def test_to_dict(self) -> None:
        """Test converting report to dict."""
        metrics = ScaleMetrics(active_contributors=5)
        
        report = ScaleReport(
            tier=ScaleTier.HEALTHY,
            metrics=metrics,
            violations=[],
            recommendations=["Keep Git strategy A"],
        )
        
        data = report.to_dict()
        
        assert data["tier"] == "healthy"
        assert "metrics" in data
        assert "recommendations" in data