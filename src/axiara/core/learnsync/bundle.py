"""Bundle export and validation for learn sync.

Handles the creation and validation of upload bundles:
- Export learn_private diff → bundle.yaml
- Provenance metadata (user-id, timestamps, observation counts)
- Customer-specific entry exclusion option
- Bundle validation (schema, credentials check)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class BundleError(Exception):
    """Raised when bundle operations fail."""
    pass


@dataclass
class BundleMetadata:
    """Metadata for an upload bundle."""
    
    user_id: str
    created_at: datetime
    bundle_version: str = "1.0"
    format: str = "yaml"
    observation_count: int = 0
    rule_count: int = 0
    excluded_count: int = 0
    scope: str = "full"  # full | generic_only
    previous_upload: datetime | None = None
    checksum: str | None = None


@dataclass
class BundleRule:
    """A rule in an upload bundle."""
    
    rule_id: str
    kind: str  # material | process_cost | cost_breakdown | pricing_tiers
    key: dict[str, Any]
    value: dict[str, Any]
    trust: str  # user_rule | stats | llm
    contributor: str
    version: int
    updated_at: datetime
    observation_count: int = 1
    supersedes: list[str] = field(default_factory=list)
    customer_specific: bool = False
    notes: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "rule_id": self.rule_id,
            "kind": self.kind,
            "key": self.key,
            "value": self.value,
            "trust": self.trust,
            "contributor": self.contributor,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
            "observation_count": self.observation_count,
            "supersedes": self.supersedes,
            "customer_specific": self.customer_specific,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BundleRule":
        """Create from dictionary.
        
        Args:
            data: Rule data dict
            
        Returns:
            BundleRule instance
        """
        return cls(
            rule_id=data["rule_id"],
            kind=data["kind"],
            key=data["key"],
            value=data["value"],
            trust=data["trust"],
            contributor=data["contributor"],
            version=data["version"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            observation_count=data.get("observation_count", 1),
            supersedes=data.get("supersedes", []),
            customer_specific=data.get("customer_specific", False),
            notes=data.get("notes"),
        )


@dataclass
class Bundle:
    """A complete upload bundle."""
    
    metadata: BundleMetadata
    rules: list[BundleRule]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "metadata": {
                "user_id": self.metadata.user_id,
                "created_at": self.metadata.created_at.isoformat(),
                "bundle_version": self.metadata.bundle_version,
                "format": self.metadata.format,
                "observation_count": self.metadata.observation_count,
                "rule_count": self.metadata.rule_count,
                "excluded_count": self.metadata.excluded_count,
                "scope": self.metadata.scope,
                "previous_upload": self.metadata.previous_upload.isoformat() if self.metadata.previous_upload else None,
                "checksum": self.metadata.checksum,
            },
            "rules": [rule.to_dict() for rule in self.rules],
        }
    
    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum of bundle contents.
        
        Returns:
            Hex checksum string
        """
        content = yaml.dump(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class BundleExporter:
    """Exports learn_private data as upload bundles.
    
    Per learn-sync-text.md §3.2:
    - Export incremental learn_private diff
    - Add provenance metadata
    - Customer-specific entries excluded by default
    - YAML format (AI-friendly)
    """
    
    def __init__(self, learn_dir: Path | None = None) -> None:
        """Initialize bundle exporter.
        
        Args:
            learn_dir: Learning data directory (default: data/learn/)
        """
        self.learn_dir = learn_dir or Path("data/learn")
        self.private_dir = self.learn_dir / "private"
    
    def load_private_rules(
        self,
        exclude_customer_specific: bool = True,
    ) -> list[BundleRule]:
        """Load rules from learn_private.
        
        Args:
            exclude_customer_specific: Whether to exclude customer-specific entries
            
        Returns:
            List of BundleRule instances
        """
        rules: list[BundleRule] = []
        
        if not self.private_dir.exists():
            return rules
        
        rules_dir = self.private_dir / "rules"
        if not rules_dir.exists():
            return rules
        
        # Load all YAML files in rules directory
        for yaml_file in rules_dir.glob("*.yaml"):
            try:
                content = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content) or {}
                
                # Handle both list and dict formats
                if isinstance(data, dict):
                    # Single rule file
                    if "rule_id" in data:
                        data = [data]
                    else:
                        # Multiple rules under a key
                        data = data.get("rules", [])
                
                for rule_data in data:
                    if isinstance(rule_data, dict):
                        rule = BundleRule.from_dict(rule_data)
                        
                        # Skip customer-specific if excluded
                        if exclude_customer_specific and rule.customer_specific:
                            continue
                        
                        rules.append(rule)
            
            except Exception:
                # Skip files that can't be parsed
                continue
        
        return rules
    
    def export_bundle(
        self,
        user_id: str,
        exclude_customer_specific: bool = True,
        previous_upload: datetime | None = None,
    ) -> Bundle:
        """Export a new upload bundle.
        
        Args:
            user_id: User ID for this upload
            exclude_customer_specific: Whether to exclude customer-specific entries
            previous_upload: Timestamp of previous upload (for incremental)
            
        Returns:
            Bundle instance ready for upload
        """
        # Load rules
        all_rules = self.load_private_rules(
            exclude_customer_specific=False,
        )
        
        # Separate rules
        included_rules = [
            r for r in all_rules
            if not (exclude_customer_specific and r.customer_specific)
        ]
        excluded_count = len(all_rules) - len(included_rules)
        
        # Calculate totals
        total_observations = sum(r.observation_count for r in included_rules)
        
        # Create metadata
        metadata = BundleMetadata(
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            observation_count=total_observations,
            rule_count=len(included_rules),
            excluded_count=excluded_count,
            scope="generic_only" if exclude_customer_specific else "full",
            previous_upload=previous_upload,
        )
        
        # Create bundle
        bundle = Bundle(
            metadata=metadata,
            rules=included_rules,
        )
        
        # Compute and set checksum
        metadata.checksum = bundle.compute_checksum()
        
        return bundle
    
    def save_bundle(self, bundle: Bundle, output_path: Path) -> None:
        """Save bundle to YAML file.
        
        Args:
            bundle: Bundle to save
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = yaml.dump(
            bundle.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        
        output_path.write_text(content, encoding="utf-8")
    
    def get_last_upload_time(self, user_id: str) -> datetime | None:
        """Get timestamp of last upload for a user.
        
        Reads from local tracking file.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Last upload timestamp or None
        """
        tracking_file = self.learn_dir / ".upload_tracking.yaml"
        
        if not tracking_file.exists():
            return None
        
        try:
            content = tracking_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
            user_data = data.get("users", {}).get(user_id, {})
            last_upload = user_data.get("last_upload")
            
            if last_upload:
                return datetime.fromisoformat(last_upload)
        
        except Exception:
            pass
        
        return None
    
    def record_upload(
        self,
        user_id: str,
        timestamp: datetime,
        bundle_path: str,
    ) -> None:
        """Record an upload in the tracking file.
        
        Args:
            user_id: User ID
            timestamp: Upload timestamp
            bundle_path: Path to bundle file
        """
        tracking_file = self.learn_dir / ".upload_tracking.yaml"
        
        # Load existing data
        data: dict[str, Any] = {}
        if tracking_file.exists():
            try:
                content = tracking_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content) or {}
            except Exception:
                data = {}
        
        # Update user data
        if "users" not in data:
            data["users"] = {}
        
        data["users"][user_id] = {
            "last_upload": timestamp.isoformat(),
            "bundle_path": bundle_path,
            "upload_count": data.get("users", {}).get(user_id, {}).get("upload_count", 0) + 1,
        }
        
        # Save
        tracking_file.parent.mkdir(parents=True, exist_ok=True)
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        tracking_file.write_text(content, encoding="utf-8")


class BundleValidator:
    """Validates upload bundles.
    
    Checks:
    - Bundle format and schema
    - Rule validity
    - No credentials in bundle
    - Checksum verification
    """
    
    FORBIDDEN_PATTERNS = [
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "credential",
        "auth",
    ]
    
    def validate_bundle(self, bundle: Bundle) -> tuple[bool, list[str]]:
        """Validate a bundle.
        
        Args:
            bundle: Bundle to validate
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors: list[str] = []
        
        # Validate metadata
        if not bundle.metadata.user_id:
            errors.append("Missing user_id in metadata")
        
        if not bundle.metadata.created_at:
            errors.append("Missing created_at in metadata")
        
        # Validate rules
        for i, rule in enumerate(bundle.rules):
            rule_errors = self._validate_rule(rule, i)
            errors.extend(rule_errors)
        
        # Check for credentials
        credential_errors = self._check_credentials(bundle)
        errors.extend(credential_errors)
        
        # Verify checksum
        if bundle.metadata.checksum:
            computed = bundle.compute_checksum()
            if computed != bundle.metadata.checksum:
                errors.append("Checksum mismatch - bundle may be corrupted")
        
        return len(errors) == 0, errors
    
    def _validate_rule(self, rule: BundleRule, index: int) -> list[str]:
        """Validate a single rule.
        
        Args:
            rule: Rule to validate
            index: Rule index for error messages
            
        Returns:
            List of validation errors
        """
        errors: list[str] = []
        prefix = f"Rule {index} ({rule.rule_id})"
        
        # Required fields
        if not rule.rule_id:
            errors.append(f"{prefix}: missing rule_id")
        
        if not rule.kind:
            errors.append(f"{prefix}: missing kind")
        elif rule.kind not in ["material", "process_cost", "cost_breakdown", "pricing_tiers"]:
            errors.append(f"{prefix}: invalid kind '{rule.kind}'")
        
        if not rule.key:
            errors.append(f"{prefix}: missing key")
        
        if not rule.value:
            errors.append(f"{prefix}: missing value")
        
        if not rule.trust:
            errors.append(f"{prefix}: missing trust")
        elif rule.trust not in ["user_rule", "stats", "llm"]:
            errors.append(f"{prefix}: invalid trust '{rule.trust}'")
        
        if not rule.contributor:
            errors.append(f"{prefix}: missing contributor")
        
        if rule.version < 1:
            errors.append(f"{prefix}: invalid version {rule.version}")
        
        if rule.observation_count < 1:
            errors.append(f"{prefix}: invalid observation_count {rule.observation_count}")
        
        return errors
    
    def _check_credentials(self, bundle: Bundle) -> list[str]:
        """Check bundle for credential-like content.
        
        Args:
            bundle: Bundle to check
            
        Returns:
            List of credential-related errors
        """
        errors: list[str] = []
        
        # Convert bundle to string for pattern matching
        content = yaml.dump(bundle.to_dict()).lower()
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in content:
                # Check if it's actually a credential value
                # (not just a field name like "requires_auth")
                lines = content.split("\n")
                for line in lines:
                    if pattern in line and ":" in line:
                        key, value = line.split(":", 1)
                        if value.strip() and not value.strip().startswith("false"):
                            errors.append(
                                f"Potential credential found: field containing '{pattern}'"
                            )
                            break
        
        return errors
    
    def load_bundle_file(self, path: Path) -> Bundle:
        """Load a bundle from YAML file.
        
        Args:
            path: Path to bundle file
            
        Returns:
            Bundle instance
            
        Raises:
            BundleError: If loading fails
        """
        if not path.exists():
            raise BundleError(f"Bundle file not found: {path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
            
            # Parse metadata
            meta_data = data.get("metadata", {})
            metadata = BundleMetadata(
                user_id=meta_data["user_id"],
                created_at=datetime.fromisoformat(meta_data["created_at"]),
                bundle_version=meta_data.get("bundle_version", "1.0"),
                format=meta_data.get("format", "yaml"),
                observation_count=meta_data.get("observation_count", 0),
                rule_count=meta_data.get("rule_count", 0),
                excluded_count=meta_data.get("excluded_count", 0),
                scope=meta_data.get("scope", "full"),
                previous_upload=(
                    datetime.fromisoformat(meta_data["previous_upload"])
                    if meta_data.get("previous_upload")
                    else None
                ),
                checksum=meta_data.get("checksum"),
            )
            
            # Parse rules
            rules = []
            for rule_data in data.get("rules", []):
                rule = BundleRule.from_dict(rule_data)
                rules.append(rule)
            
            return Bundle(metadata=metadata, rules=rules)
        
        except Exception as e:
            raise BundleError(f"Failed to load bundle: {e}") from e