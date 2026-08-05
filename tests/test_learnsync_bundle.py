"""Tests for bundle export and validation (learn sync).

Tests for:
- Bundle export from learn_private
- Bundle validation
- Checksum verification
- Customer-specific entry exclusion
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from axiara.core.learnsync.bundle import (
    Bundle,
    BundleError,
    BundleExporter,
    BundleMetadata,
    BundleRule,
    BundleValidator,
)


class TestBundleRule:
    """Tests for BundleRule."""
    
    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        rule = BundleRule(
            rule_id="pc-0001",
            kind="process_cost",
            key={"material": "copper-wire", "process": "cutting"},
            value={"unit_fee": 0.35, "loss_rate": 0.03},
            trust="user_rule",
            contributor="AX-abcd-1234",
            version=1,
            updated_at=datetime(2026, 8, 5, 12, 0, 0),
        )
        
        data = rule.to_dict()
        
        assert data["rule_id"] == "pc-0001"
        assert data["kind"] == "process_cost"
        assert data["key"]["material"] == "copper-wire"
        assert data["trust"] == "user_rule"
        assert "updated_at" in data
    
    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "rule_id": "pc-0002",
            "kind": "material",
            "key": {"alias": "铜线", "canonical": "copper-wire"},
            "value": {"material": "copper-wire"},
            "trust": "stats",
            "contributor": "AX-1234-5678",
            "version": 2,
            "updated_at": "2026-08-05T14:00:00",
            "observation_count": 5,
        }
        
        rule = BundleRule.from_dict(data)
        
        assert rule.rule_id == "pc-0002"
        assert rule.kind == "material"
        assert rule.trust == "stats"
        assert rule.observation_count == 5


class TestBundleExporter:
    """Tests for BundleExporter."""
    
    def test_export_bundle_empty(self) -> None:
        """Test exporting when no private rules exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learn_dir = Path(tmpdir)
            exporter = BundleExporter(learn_dir=learn_dir)
            
            bundle = exporter.export_bundle(user_id="AX-test-1234")
            
            assert bundle.metadata.user_id == "AX-test-1234"
            assert len(bundle.rules) == 0
    
    def test_export_bundle_with_rules(self) -> None:
        """Test exporting bundle with rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learn_dir = Path(tmpdir)
            private_dir = learn_dir / "private" / "rules"
            private_dir.mkdir(parents=True)
            
            # Create a rule file
            rule_data = {
                "rule_id": "pc-0001",
                "kind": "process_cost",
                "key": {"material": "copper-wire", "process": "cutting"},
                "value": {"unit_fee": 0.35, "loss_rate": 0.03},
                "trust": "user_rule",
                "contributor": "AX-test-1234",
                "version": 1,
                "updated_at": "2026-08-05T12:00:00",
            }
            
            rule_file = private_dir / "process-cost.yaml"
            rule_file.write_text(yaml.dump([rule_data]))
            
            exporter = BundleExporter(learn_dir=learn_dir)
            bundle = exporter.export_bundle(user_id="AX-test-1234")
            
            assert len(bundle.rules) == 1
            assert bundle.rules[0].rule_id == "pc-0001"
    
    def test_export_excludes_customer_specific(self) -> None:
        """Test that customer-specific entries are excluded by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learn_dir = Path(tmpdir)
            private_dir = learn_dir / "private" / "rules"
            private_dir.mkdir(parents=True)
            
            # Create rules - one regular, one customer-specific
            rules = [
                {
                    "rule_id": "pc-0001",
                    "kind": "process_cost",
                    "key": {"material": "copper-wire", "process": "cutting"},
                    "value": {"unit_fee": 0.35},
                    "trust": "user_rule",
                    "contributor": "AX-test-1234",
                    "version": 1,
                    "updated_at": "2026-08-05T12:00:00",
                },
                {
                    "rule_id": "pc-0002",
                    "kind": "process_cost",
                    "key": {"material": "copper-wire", "process": "cutting"},
                    "value": {"unit_fee": 0.40},
                    "trust": "user_rule",
                    "contributor": "AX-test-1234",
                    "version": 1,
                    "updated_at": "2026-08-05T12:00:00",
                    "customer_specific": True,
                },
            ]
            
            rule_file = private_dir / "process-cost.yaml"
            rule_file.write_text(yaml.dump(rules))
            
            exporter = BundleExporter(learn_dir=learn_dir)
            
            # Default: exclude customer-specific
            bundle1 = exporter.export_bundle(user_id="AX-test-1234", exclude_customer_specific=True)
            assert len(bundle1.rules) == 1
            assert bundle1.metadata.excluded_count == 1
            
            # Include all
            bundle2 = exporter.export_bundle(user_id="AX-test-1234", exclude_customer_specific=False)
            assert len(bundle2.rules) == 2
    
    def test_save_and_load_bundle(self) -> None:
        """Test saving and loading bundle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            learn_dir = Path(tmpdir)
            exporter = BundleExporter(learn_dir=learn_dir)
            
            # Create bundle
            metadata = BundleMetadata(
                user_id="AX-test-1234",
                created_at=datetime.utcnow(),
                rule_count=2,
            )
            
            rules = [
                BundleRule(
                    rule_id="pc-0001",
                    kind="process_cost",
                    key={"material": "copper-wire"},
                    value={"unit_fee": 0.35},
                    trust="user_rule",
                    contributor="AX-test-1234",
                    version=1,
                    updated_at=datetime.utcnow(),
                ),
                BundleRule(
                    rule_id="pc-0002",
                    kind="material",
                    key={"alias": "铜线"},
                    value={"canonical": "copper-wire"},
                    trust="stats",
                    contributor="AX-test-1234",
                    version=1,
                    updated_at=datetime.utcnow(),
                ),
            ]
            
            bundle = Bundle(metadata=metadata, rules=rules)
            
            # Save
            bundle_path = Path(tmpdir) / "bundle.yaml"
            exporter.save_bundle(bundle, bundle_path)
            
            assert bundle_path.exists()
            
            # Load and verify
            validator = BundleValidator()
            loaded = validator.load_bundle_file(bundle_path)
            
            assert loaded.metadata.user_id == "AX-test-1234"
            assert len(loaded.rules) == 2
    
    def test_bundle_checksum(self) -> None:
        """Test bundle checksum computation."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime(2026, 8, 5, 12, 0, 0),
        )
        
        bundle = Bundle(metadata=metadata, rules=[])
        
        checksum1 = bundle.compute_checksum()
        checksum2 = bundle.compute_checksum()
        
        # Should be consistent
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length


class TestBundleValidator:
    """Tests for BundleValidator."""
    
    def test_validate_valid_bundle(self) -> None:
        """Test validation of valid bundle."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime.utcnow(),
        )
        
        rules = [
            BundleRule(
                rule_id="pc-0001",
                kind="process_cost",
                key={"material": "copper-wire"},
                value={"unit_fee": 0.35},
                trust="user_rule",
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.utcnow(),
            ),
        ]
        
        bundle = Bundle(metadata=metadata, rules=rules)
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_missing_fields(self) -> None:
        """Test validation catches missing required fields."""
        metadata = BundleMetadata(
            user_id="",  # Missing
            created_at=datetime.utcnow(),
        )
        
        rules = [
            BundleRule(
                rule_id="",  # Missing
                kind="process_cost",
                key={},
                value={},
                trust="",
                contributor="",
                version=0,  # Invalid
                updated_at=datetime.utcnow(),
            ),
        ]
        
        bundle = Bundle(metadata=metadata, rules=rules)
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_invalid_kind(self) -> None:
        """Test validation catches invalid kind."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime.utcnow(),
        )
        
        rules = [
            BundleRule(
                rule_id="pc-0001",
                kind="invalid_kind",  # Invalid
                key={"material": "copper-wire"},
                value={"unit_fee": 0.35},
                trust="user_rule",
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.utcnow(),
            ),
        ]
        
        bundle = Bundle(metadata=metadata, rules=rules)
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        assert not is_valid
        assert any("invalid kind" in e.lower() for e in errors)
    
    def test_validate_invalid_trust(self) -> None:
        """Test validation catches invalid trust level."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime.utcnow(),
        )
        
        rules = [
            BundleRule(
                rule_id="pc-0001",
                kind="process_cost",
                key={"material": "copper-wire"},
                value={"unit_fee": 0.35},
                trust="invalid_trust",  # Invalid
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.utcnow(),
            ),
        ]
        
        bundle = Bundle(metadata=metadata, rules=rules)
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        assert not is_valid
        assert any("invalid trust" in e.lower() for e in errors)
    
    def test_validate_checksum_mismatch(self) -> None:
        """Test validation catches checksum mismatch."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime.utcnow(),
            checksum="invalid-checksum-123",  # Wrong
        )
        
        bundle = Bundle(metadata=metadata, rules=[])
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        assert not is_valid
        assert any("checksum" in e.lower() for e in errors)
    
    def test_validate_no_credentials(self) -> None:
        """Test that bundles with credentials are rejected."""
        metadata = BundleMetadata(
            user_id="AX-test-1234",
            created_at=datetime.utcnow(),
        )
        
        # Rule with credential-like value
        rules = [
            BundleRule(
                rule_id="pc-0001",
                kind="process_cost",
                key={"material": "copper-wire"},
                value={"api_key": "secret123"},  # Credential-like
                trust="user_rule",
                contributor="AX-test-1234",
                version=1,
                updated_at=datetime.utcnow(),
            ),
        ]
        
        bundle = Bundle(metadata=metadata, rules=rules)
        
        validator = BundleValidator()
        is_valid, errors = validator.validate_bundle(bundle)
        
        # Should detect potential credential
        assert any("credential" in e.lower() for e in errors)