"""Central review flow for learn sync.

Handles the review process:
- Ingest bundles from all user branches
- Compare against learn_shared rules
- Generate proposals (ADD / UPDATE / REJECT)
- Admin confirmation gate
- Apply approved changes to learn_shared
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from axiara.core.learnsync.bundle import Bundle, BundleValidator


class ProposalType(StrEnum):
    """Type of change proposal."""
    
    ADD = "ADD"
    UPDATE = "UPDATE"
    REJECT = "REJECT"


@dataclass
class Proposal:
    """A change proposal from review."""
    
    proposal_type: ProposalType
    rule_id: str
    kind: str
    contributor: str
    version: int
    trust: str
    reason: str = ""
    diff: dict[str, Any] | None = None
    existing_version: int | None = None
    rule_data: dict[str, Any] | None = None


@dataclass
class ReviewSession:
    """A review session with all proposals."""
    
    review_date: datetime
    contributors: list[str]
    bundles_processed: int
    proposals: list[Proposal]
    inbox_path: str
    status: str = "pending"  # pending | confirmed | applied
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "review_date": self.review_date.isoformat(),
            "contributors": self.contributors,
            "bundles_processed": self.bundles_processed,
            "status": self.status,
            "inbox_path": self.inbox_path,
            "proposals": [
                {
                    "type": p.proposal_type.value,
                    "rule_id": p.rule_id,
                    "kind": p.kind,
                    "contributor": p.contributor,
                    "version": p.version,
                    "trust": p.trust,
                    "reason": p.reason,
                    "diff": p.diff,
                    "existing_version": p.existing_version,
                    "rule_data": p.rule_data,
                }
                for p in self.proposals
            ],
        }


class ReviewManager:
    """Manages central review flow.
    
    Per learn-sync-text.md §4:
    1. Ingest bundles from all user/* branches
    2. Compare against learn_shared
    3. Propose changes (ADD/UPDATE/REJECT)
    4. Admin confirms
    5. Apply to learn_shared
    """
    
    def __init__(
        self,
        store_dir: Path | None = None,
        main_dir: Path | None = None,
    ) -> None:
        """Initialize review manager.
        
        Args:
            store_dir: Store directory (default: .data/store/)
            main_dir: Main data directory (default: data/main/)
        """
        self.store_dir = store_dir or Path(".data/store")
        self.main_dir = main_dir or Path("data/main")
        self.learn_shared_dir = self.store_dir / "learn_shared"
        self.rules_dir = self.learn_shared_dir / "rules"
        self.validator = BundleValidator()
    
    def ingest_bundles(self) -> list[Bundle]:
        """Load all bundles from user branches.
        
        Fetches refs/heads/user/* and reads all bundles.
        
        Returns:
            List of Bundle instances
        """
        bundles: list[Bundle] = []
        inbox_dir = self.store_dir / "learn_inbox"
        
        if not inbox_dir.exists():
            return bundles
        
        # Find all bundle.yaml files
        for bundle_file in inbox_dir.glob("*/./*/bundle.yaml"):
            try:
                bundle = self.validator.load_bundle_file(bundle_file)
                is_valid, errors = self.validator.validate_bundle(bundle)
                
                if is_valid:
                    bundles.append(bundle)
                # Skip invalid bundles (log if needed)
            
            except Exception:
                # Skip bundles that can't be loaded
                continue
        
        return bundles
    
    def load_learn_shared(self) -> dict[str, dict[str, Any]]:
        """Load all rules from learn_shared.
        
        Returns:
            Dict mapping rule_id to rule data
        """
        rules: dict[str, dict[str, Any]] = {}
        
        if not self.rules_dir.exists():
            return rules
        
        # Load all YAML files in rules directory
        for yaml_file in self.rules_dir.glob("*.yaml"):
            try:
                content = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content) or {}
                
                # Handle both list and dict formats
                if isinstance(data, dict):
                    if "rule_id" in data:
                        # Single rule file
                        rules[data["rule_id"]] = data
                    else:
                        # Multiple rules under a key
                        for rule in data.get("rules", []):
                            if isinstance(rule, dict) and "rule_id" in rule:
                                rules[rule["rule_id"]] = rule
                elif isinstance(data, list):
                    for rule in data:
                        if isinstance(rule, dict) and "rule_id" in rule:
                            rules[rule["rule_id"]] = rule
            
            except Exception:
                continue
        
        return rules
    
    def compare_rules(
        self,
        bundle: Bundle,
        existing_rules: dict[str, dict[str, Any]],
        main_baseline: dict[str, dict[str, Any]],
    ) -> list[Proposal]:
        """Compare bundle rules against existing rules.
        
        Args:
            bundle: Upload bundle
            existing_rules: Existing learn_shared rules
            main_baseline: Official baseline rules
            
        Returns:
            List of proposals
        """
        proposals: list[Proposal] = []
        
        for rule in bundle.rules:
            rule_id = rule.rule_id
            
            # Check if rule exists
            if rule_id in existing_rules:
                existing = existing_rules[rule_id]
                proposal = self._compare_existing(rule, existing)
            else:
                # New rule
                proposal = self._propose_add(rule, main_baseline)
            
            if proposal:
                proposals.append(proposal)
        
        return proposals
    
    def _compare_existing(
        self,
        new_rule: Any,
        existing: dict[str, Any],
    ) -> Proposal:
        """Compare new rule against existing.
        
        Args:
            new_rule: New rule from bundle
            existing: Existing rule in learn_shared
            
        Returns:
            Proposal for update or reject
        """
        existing_version = existing.get("version", 1)
        existing_trust = existing.get("trust", "stats")
        
        # Trust hierarchy: user_rule > stats > llm
        trust_order = {"user_rule": 3, "stats": 2, "llm": 1}
        
        # Check if new rule should update existing
        should_update = False
        reason = ""
        
        if new_rule.version > existing_version:
            if trust_order.get(new_rule.trust, 0) >= trust_order.get(existing_trust, 0):
                should_update = True
                reason = f"Newer version ({new_rule.version} > {existing_version})"
        
        if new_rule.trust == "user_rule" and existing_trust != "user_rule":
            should_update = True
            reason = f"Higher trust level ({new_rule.trust} > {existing_trust})"
        
        if should_update:
            # Compute diff
            diff = {
                "from": existing,
                "to": new_rule.to_dict(),
            }
            
            return Proposal(
                proposal_type=ProposalType.UPDATE,
                rule_id=new_rule.rule_id,
                kind=new_rule.kind,
                contributor=new_rule.contributor,
                version=new_rule.version,
                trust=new_rule.trust,
                reason=reason,
                diff=diff,
                existing_version=existing_version,
                rule_data=new_rule.to_dict(),
            )
        
        # Reject: existing is newer or same trust
        return Proposal(
            proposal_type=ProposalType.REJECT,
            rule_id=new_rule.rule_id,
            kind=new_rule.kind,
            contributor=new_rule.contributor,
            version=new_rule.version,
            trust=new_rule.trust,
            reason=f"Existing rule is newer (v{existing_version}) or same trust",
            existing_version=existing_version,
        )
    
    def _propose_add(
        self,
        rule: Any,
        main_baseline: dict[str, dict[str, Any]],
    ) -> Proposal:
        """Propose adding a new rule.
        
        Checks against official baseline for conflicts.
        
        Args:
            rule: New rule to add
            main_baseline: Official baseline rules
            
        Returns:
            Proposal for add or reject
        """
        # Check for conflicts with main baseline
        # (Rules shouldn't contradict official baseline)
        rule_key = rule.key
        conflicts = []
        
        for baseline_rule in main_baseline.values():
            if baseline_rule.get("kind") == rule.kind:
                baseline_key = baseline_rule.get("key", {})
                # Simple conflict detection: same material
                if rule_key.get("material") == baseline_key.get("material"):
                    # Check value consistency
                    baseline_value = baseline_rule.get("value", {})
                    rule_value = rule.value
                    
                    # Significant price difference would be a conflict
                    if "unit_fee" in baseline_value and "unit_fee" in rule_value:
                        diff_ratio = abs(
                            rule_value["unit_fee"] - baseline_value["unit_fee"]
                        ) / max(baseline_value["unit_fee"], 0.001)
                        
                        if diff_ratio > 0.5:  # More than 50% difference
                            conflicts.append(
                                f"Conflicts with baseline rule {baseline_rule.get('rule_id')}"
                            )
        
        if conflicts:
            return Proposal(
                proposal_type=ProposalType.REJECT,
                rule_id=rule.rule_id,
                kind=rule.kind,
                contributor=rule.contributor,
                version=rule.version,
                trust=rule.trust,
                reason=f"Contradicts official baseline: {', '.join(conflicts)}",
                rule_data=rule.to_dict(),
            )
        
        # Valid new rule
        return Proposal(
            proposal_type=ProposalType.ADD,
            rule_id=rule.rule_id,
            kind=rule.kind,
            contributor=rule.contributor,
            version=rule.version,
            trust=rule.trust,
            reason="New rule candidate",
            rule_data=rule.to_dict(),
        )
    
    def run_review(self) -> ReviewSession:
        """Run full review process.
        
        Returns:
            ReviewSession with all proposals
        """
        # Load bundles
        bundles = self.ingest_bundles()
        
        # Load existing rules
        existing_rules = self.load_learn_shared()
        
        # Load main baseline (for conflict detection)
        main_baseline = self._load_main_baseline()
        
        # Collect all proposals
        all_proposals: list[Proposal] = []
        contributors: set[str] = set()
        
        for bundle in bundles:
            contributors.add(bundle.metadata.user_id)
            proposals = self.compare_rules(bundle, existing_rules, main_baseline)
            all_proposals.extend(proposals)
        
        # Create review session
        review_date = datetime.utcnow()
        inbox_path = f"learn_inbox/_reviews/{review_date.strftime('%Y%m%d')}"
        
        session = ReviewSession(
            review_date=review_date,
            contributors=list(contributors),
            bundles_processed=len(bundles),
            proposals=all_proposals,
            inbox_path=inbox_path,
        )
        
        return session
    
    def _load_main_baseline(self) -> dict[str, dict[str, Any]]:
        """Load official baseline rules.
        
        Returns:
            Dict mapping rule_id to rule data
        """
        rules: dict[str, dict[str, Any]] = {}
        
        if not self.main_dir.exists():
            return rules
        
        # Load all YAML files in main
        for yaml_file in self.main_dir.glob("**/*.yaml"):
            try:
                content = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(content) or {}
                
                if isinstance(data, dict) and "rule_id" in data:
                    rules[data["rule_id"]] = data
            
            except Exception:
                continue
        
        return rules
    
    def save_proposals(self, session: ReviewSession) -> Path:
        """Save proposals to file for admin review.
        
        Args:
            session: Review session
            
        Returns:
            Path to proposals file
        """
        proposals_path = self.store_dir / session.inbox_path / "proposals.yaml"
        proposals_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = yaml.dump(
            session.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        
        proposals_path.write_text(content, encoding="utf-8")
        
        return proposals_path
    
    def apply_proposals(
        self,
        session: ReviewSession,
        accepted_rule_ids: list[str],
    ) -> dict[str, Any]:
        """Apply accepted proposals to learn_shared.
        
        Args:
            session: Review session
            accepted_rule_ids: List of rule_ids to apply
            
        Returns:
            Dict with apply results
        """
        applied: list[str] = []
        rejected: list[str] = []
        
        # Ensure rules directory exists
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        
        # Group rules by kind
        rules_by_kind: dict[str, list[dict[str, Any]]] = {}
        
        for proposal in session.proposals:
            if proposal.rule_id in accepted_rule_ids:
                if proposal.proposal_type in (ProposalType.ADD, ProposalType.UPDATE):
                    kind = proposal.kind
                    if kind not in rules_by_kind:
                        rules_by_kind[kind] = []
                    
                    if proposal.rule_data:
                        rules_by_kind[kind].append(proposal.rule_data)
                        applied.append(proposal.rule_id)
                else:
                    rejected.append(proposal.rule_id)
        
        # Write rules files
        for kind, rules in rules_by_kind.items():
            filename = f"{kind.replace('_', '-')}.yaml"
            filepath = self.rules_dir / filename
            
            # Load existing rules
            existing_rules: list[dict[str, Any]] = []
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding="utf-8")
                    data = yaml.safe_load(content) or []
                    if isinstance(data, list):
                        existing_rules = data
                except Exception:
                    pass
            
            # Merge rules
            existing_ids = {r.get("rule_id") for r in existing_rules}
            for new_rule in rules:
                rule_id = new_rule.get("rule_id")
                if rule_id in existing_ids:
                    # Update existing
                    for i, rule in enumerate(existing_rules):
                        if rule.get("rule_id") == rule_id:
                            existing_rules[i] = new_rule
                            break
                else:
                    # Add new
                    existing_rules.append(new_rule)
            
            # Save
            content = yaml.dump(
                existing_rules,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
            filepath.write_text(content, encoding="utf-8")
        
        # Update manifest
        self._update_manifest()
        
        # Update session status
        session.status = "applied"
        
        return {
            "applied": applied,
            "rejected": rejected,
            "rules_updated": len(applied),
        }
    
    def _update_manifest(self) -> None:
        """Update manifest.json with checksums."""
        import hashlib
        import json
        
        manifest_path = self.learn_shared_dir / "manifest.json"
        checksums: dict[str, str] = {}
        
        # Calculate checksums for all rule files
        if self.rules_dir.exists():
            for rule_file in self.rules_dir.glob("*.yaml"):
                content = rule_file.read_bytes()
                checksum = hashlib.sha256(content).hexdigest()
                rel_path = rule_file.relative_to(self.learn_shared_dir)
                checksums[str(rel_path)] = checksum
        
        # Create manifest
        manifest = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "checksums": checksums,
        }
        
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
    
    def get_proposal_summary(self, session: ReviewSession) -> dict[str, Any]:
        """Get summary of proposals for admin review.
        
        Args:
            session: Review session
            
        Returns:
            Dict with proposal summary
        """
        adds = [p for p in session.proposals if p.proposal_type == ProposalType.ADD]
        updates = [p for p in session.proposals if p.proposal_type == ProposalType.UPDATE]
        rejects = [p for p in session.proposals if p.proposal_type == ProposalType.REJECT]
        
        return {
            "review_date": session.review_date.isoformat(),
            "contributors": session.contributors,
            "bundles_processed": session.bundles_processed,
            "total_proposals": len(session.proposals),
            "adds": len(adds),
            "updates": len(updates),
            "rejects": len(rejects),
            "add_details": [
                {"rule_id": p.rule_id, "contributor": p.contributor}
                for p in adds
            ],
            "update_details": [
                {
                    "rule_id": p.rule_id,
                    "contributor": p.contributor,
                    "existing_version": p.existing_version,
                    "new_version": p.version,
                }
                for p in updates
            ],
        }