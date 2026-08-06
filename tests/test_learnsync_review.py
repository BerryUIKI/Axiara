"""Tests for central review flow (learn sync).

Tests for:
- Bundle ingestion
- Rule comparison
- Proposal generation
- Apply operations
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from axiara.core.learnsync.bundle import Bundle, BundleMetadata, BundleRule
from axiara.core.learnsync.review import (
    Proposal,
    ProposalType,
    ReviewManager,
    ReviewSession,
)


class TestReviewManager:
    """Tests for ReviewManager."""
    
    def test_ingest_bundles_empty(self) -> None:
        """Test ingesting when no bundles exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            bundles = manager.ingest_bundles()
            
            assert bundles == []
    
    def test_ingest_bundles_with_files(self) -> None:
        """Test ingesting existing bundles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            # Create bundle files
            inbox_dir = store_dir / "learn_inbox" / "AX-test-1234" / "20260805"
            inbox_dir.mkdir(parents=True)
            
            bundle_data = {
                "metadata": {
                    "user_id": "AX-test-1234",
                    "created_at": "2026-08-05T12:00:00",
                    "bundle_version": "1.0",
                    "rule_count": 1,
                },
                "rules": [
                    {
                        "rule_id": "pc-0001",
                        "kind": "process_cost",
                        "key": {"material": "copper-wire", "process": "cutting"},
                        "value": {"unit_fee": 0.35},
                        "trust": "user_rule",
                        "contributor": "AX-test-1234",
                        "version": 1,
                        "updated_at": "2026-08-05T12:00:00",
                    }
                ],
            }
            
            bundle_file = inbox_dir / "bundle.yaml"
            bundle_file.write_text(yaml.dump(bundle_data))
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            bundles = manager.ingest_bundles()
            
            assert len(bundles) == 1
            assert bundles[0].metadata.user_id == "AX-test-1234"
    
    def test_load_learn_shared_empty(self) -> None:
        """Test loading empty learn_shared."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            rules = manager.load_learn_shared()
            
            assert rules == {}
    
    def test_load_learn_shared_with_rules(self) -> None:
        """Test loading existing learn_shared rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            # Create learn_shared rules
            rules_dir = store_dir / "learn_shared" / "rules"
            rules_dir.mkdir(parents=True)
            
            rule_data = {
                "rule_id": "pc-0001",
                "kind": "process_cost",
                "key": {"material": "copper-wire", "process": "cutting"},
                "value": {"unit_fee": 0.30},
                "trust": "stats",
                "contributor": "system",
                "version": 1,
                "updated_at": "2026-08-01T12:00:00",
            }
            
            rule_file = rules_dir / "process-cost.yaml"
            rule_file.write_text(yaml.dump([rule_data]))
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            rules = manager.load_learn_shared()
            
            assert "pc-0001" in rules
            assert rules["pc-0001"]["value"]["unit_fee"] == 0.30
    
    def test_compare_rules_add_new(self) -> None:
        """Test comparing rules - new rule should be ADD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            # Create bundle with new rule
            metadata = BundleMetadata(
                user_id="AX-test-1234",
                created_at=datetime.now(timezone.utc),
            )
            
            new_rule = BundleRule(
                rule_id="pc-new-001",
                kind="process_cost",
                key={"material": "aluminum-plate", "process": "cutting"},
                value={"unit_fee": 0.25},
                trust="user_rule",
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.now(timezone.utc),
            )
            
            bundle = Bundle(metadata=metadata, rules=[new_rule])
            
            proposals = manager.compare_rules(bundle, {}, {})
            
            assert len(proposals) == 1
            assert proposals[0].proposal_type == ProposalType.ADD
            assert proposals[0].rule_id == "pc-new-001"
    
    def test_compare_rules_update_existing(self) -> None:
        """Test comparing rules - newer version should be UPDATE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            # Existing rule
            existing_rules = {
                "pc-0001": {
                    "rule_id": "pc-0001",
                    "kind": "process_cost",
                    "key": {"material": "copper-wire", "process": "cutting"},
                    "value": {"unit_fee": 0.30},
                    "trust": "stats",
                    "contributor": "system",
                    "version": 1,
                    "updated_at": "2026-08-01T12:00:00",
                }
            }
            
            # New version of same rule
            metadata = BundleMetadata(
                user_id="AX-test-1234",
                created_at=datetime.now(timezone.utc),
            )
            
            new_rule = BundleRule(
                rule_id="pc-0001",
                kind="process_cost",
                key={"material": "copper-wire", "process": "cutting"},
                value={"unit_fee": 0.35},
                trust="user_rule",
                contributor="AX-test-1234",
                version=2,
                updated_at=datetime.now(timezone.utc),
            )
            
            bundle = Bundle(metadata=metadata, rules=[new_rule])
            
            proposals = manager.compare_rules(bundle, existing_rules, {})
            
            assert len(proposals) == 1
            assert proposals[0].proposal_type == ProposalType.UPDATE
            assert proposals[0].version == 2
    
    def test_compare_rules_reject_older(self) -> None:
        """Test comparing rules - older version should be REJECT."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            # Existing rule (version 2)
            existing_rules = {
                "pc-0001": {
                    "rule_id": "pc-0001",
                    "kind": "process_cost",
                    "key": {"material": "copper-wire", "process": "cutting"},
                    "value": {"unit_fee": 0.35},
                    "trust": "stats",
                    "contributor": "system",
                    "version": 2,
                    "updated_at": "2026-08-05T12:00:00",
                }
            }
            
            # Older version
            metadata = BundleMetadata(
                user_id="AX-test-1234",
                created_at=datetime.now(timezone.utc),
            )
            
            old_rule = BundleRule(
                rule_id="pc-0001",
                kind="process_cost",
                key={"material": "copper-wire", "process": "cutting"},
                value={"unit_fee": 0.30},
                trust="stats",
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.now(timezone.utc),
            )
            
            bundle = Bundle(metadata=metadata, rules=[old_rule])
            
            proposals = manager.compare_rules(bundle, existing_rules, {})
            
            assert len(proposals) == 1
            assert proposals[0].proposal_type == ProposalType.REJECT
    
    def test_run_review(self) -> None:
        """Test running full review process."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            session = manager.run_review()
            
            assert session.status == "pending"
            assert isinstance(session.proposals, list)
    
    def test_save_and_load_proposals(self) -> None:
        """Test saving proposals to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            # Create session
            session = ReviewSession(
                review_date=datetime.now(timezone.utc),
                contributors=["AX-test-1234"],
                bundles_processed=1,
                proposals=[
                    Proposal(
                        proposal_type=ProposalType.ADD,
                        rule_id="pc-0001",
                        kind="process_cost",
                        contributor="AX-test-1234",
                        version=1,
                        trust="user_rule",
                    )
                ],
                inbox_path="learn_inbox/_reviews/20260805",
            )
            
            proposals_path = manager.save_proposals(session)
            
            assert proposals_path.exists()
            
            # Load and verify
            content = proposals_path.read_text()
            data = yaml.safe_load(content)
            
            assert len(data["proposals"]) == 1
            assert data["proposals"][0]["type"] == "ADD"
    
    def test_apply_proposals(self) -> None:
        """Test applying accepted proposals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "store"
            main_dir = Path(tmpdir) / "main"
            
            manager = ReviewManager(store_dir=store_dir, main_dir=main_dir)
            
            # Create session with proposals
            session = ReviewSession(
                review_date=datetime.now(timezone.utc),
                contributors=["AX-test-1234"],
                bundles_processed=1,
                proposals=[
                    Proposal(
                        proposal_type=ProposalType.ADD,
                        rule_id="pc-0001",
                        kind="process_cost",
                        contributor="AX-test-1234",
                        version=1,
                        trust="user_rule",
                        rule_data={
                            "rule_id": "pc-0001",
                            "kind": "process_cost",
                            "key": {"material": "copper-wire"},
                            "value": {"unit_fee": 0.35},
                            "trust": "user_rule",
                            "contributor": "AX-test-1234",
                            "version": 1,
                            "updated_at": "2026-08-05T12:00:00",
                        },
                    )
                ],
                inbox_path="learn_inbox/_reviews/20260805",
            )
            
            # Apply
            result = manager.apply_proposals(session, ["pc-0001"])
            
            assert result["rules_updated"] == 1
            assert "pc-0001" in result["applied"]
            
            # Check rule file exists
            rules_dir = store_dir / "learn_shared" / "rules"
            assert rules_dir.exists()
            
            rule_file = rules_dir / "process-cost.yaml"
            assert rule_file.exists()


class TestProposal:
    """Tests for Proposal."""
    
    def test_proposal_creation(self) -> None:
        """Test creating a proposal."""
        proposal = Proposal(
            proposal_type=ProposalType.ADD,
            rule_id="pc-0001",
            kind="process_cost",
            contributor="AX-test-1234",
            version=1,
            trust="user_rule",
            reason="New rule candidate",
        )
        
        assert proposal.proposal_type == ProposalType.ADD
        assert proposal.rule_id == "pc-0001"
        assert proposal.reason == "New rule candidate"