"""User identity management for learn sync.

Generates and manages a stable user-id for the hub model:
- Created once at onboarding
- Persisted in local_config
- Machine code as fallback
- Sanitized to [a-zA-Z0-9_-]
"""

from __future__ import annotations

import hashlib
import platform
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class UserIdError(Exception):
    """Raised when user-id operations fail."""
    pass


@dataclass
class UserIdInfo:
    """Information about a user-id."""
    
    user_id: str
    machine_code: str | None = None
    created_at: datetime | None = None
    source: str = "generated"  # generated | config | machine_code


class UserIdManager:
    """Manages stable user identity for the hub model.
    
    User-id requirements (per learn-sync-text.md §3.2):
    - Stable: generated once at onboarding, survives machine changes
    - Persisted in local_config (survives reinstalls)
    - Machine code as default/fallback
    - Sanitized to [a-zA-Z0-9_-]
    
    Format: AX-<random-hex> (e.g., AX-3f8a-c2d1)
    """
    
    USER_ID_PREFIX = "AX-"
    USER_ID_PATTERN = re.compile(r"^AX-[a-f0-9]{4}-[a-f0-9]{4}$")
    
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize user-id manager.
        
        Args:
            config_dir: Configuration directory (default: .data/local_config/)
        """
        self.config_dir = config_dir or Path(".data/local_config")
        self.config_file = self.config_dir / "config.yaml"
    
    def generate_user_id(self) -> str:
        """Generate a new unique user-id.
        
        Returns:
            New user-id in format AX-xxxx-yyyy
        """
        # Generate random hex components
        random_bytes = uuid.uuid4().bytes
        part1 = hashlib.sha256(random_bytes).hexdigest()[:4]
        part2 = hashlib.sha256(random_bytes + b"2").hexdigest()[:4]
        
        return f"{self.USER_ID_PREFIX}{part1}-{part2}"
    
    def get_machine_code(self) -> str:
        """Get a machine-unique identifier as fallback.
        
        Uses platform-specific identifiers:
        - Machine UUID on most systems
        - Fallback to hostname + MAC hash
        
        Returns:
            Machine code string
        """
        # Try platform-specific machine ID
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        line = line.strip()
                        if line and line != "UUID":
                            return self._sanitize_id(f"MC-{line[:16]}")
            
            elif platform.system() == "Linux":
                # Try /etc/machine-id
                try:
                    machine_id = Path("/etc/machine-id").read_text().strip()
                    if machine_id:
                        return self._sanitize_id(f"MC-{machine_id[:16]}")
                except FileNotFoundError:
                    pass
                
                # Try /var/lib/dbus/machine-id
                try:
                    machine_id = Path("/var/lib/dbus/machine-id").read_text().strip()
                    if machine_id:
                        return self._sanitize_id(f"MC-{machine_id[:16]}")
                except FileNotFoundError:
                    pass
            
            elif platform.system() == "Darwin":
                # macOS - use IOPlatformUUID
                import subprocess
                result = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "IOPlatformUUID" in line:
                            # Extract UUID from line
                            parts = line.split('"')
                            if len(parts) >= 4:
                                return self._sanitize_id(f"MC-{parts[-2][:16]}")
        
        except Exception:
            pass
        
        # Fallback: hostname + process hash
        hostname = platform.node() or "unknown"
        host_hash = hashlib.sha256(hostname.encode()).hexdigest()[:12]
        return self._sanitize_id(f"MC-{host_hash}")
    
    def _sanitize_id(self, raw_id: str) -> str:
        """Sanitize an ID to valid characters.
        
        Args:
            raw_id: Raw ID string
            
        Returns:
            Sanitized ID (only [a-zA-Z0-9_-])
        """
        # Replace invalid characters with hyphens
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", raw_id)
        # Collapse multiple hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")
        
        return sanitized or "AX-unknown"
    
    def load_config(self) -> dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dict (empty if file doesn't exist)
        """
        if not self.config_file.exists():
            return {}
        
        try:
            content = self.config_file.read_text(encoding="utf-8")
            config = yaml.safe_load(content) or {}
            return config
        except Exception as e:
            raise UserIdError(f"Failed to load config: {e}") from e
    
    def save_config(self, config: dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration dict to save
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            content = yaml.dump(config, default_flow_style=False, sort_keys=False)
            self.config_file.write_text(content, encoding="utf-8")
        except Exception as e:
            raise UserIdError(f"Failed to save config: {e}") from e
    
    def get_user_id(self) -> UserIdInfo:
        """Get the user-id, generating if needed.
        
        Priority:
        1. Existing user-id in config
        2. Generate new user-id and save
        
        Returns:
            UserIdInfo with the user-id
        """
        config = self.load_config()
        
        # Check for existing user-id in app section
        app_config = config.get("app", {})
        existing_id = app_config.get("user_id")
        
        if existing_id and self.USER_ID_PATTERN.match(existing_id):
            return UserIdInfo(
                user_id=existing_id,
                source="config",
            )
        
        # Generate new user-id
        new_id = self.generate_user_id()
        machine_code = self.get_machine_code()
        
        # Save to config
        if "app" not in config:
            config["app"] = {}
        
        config["app"]["user_id"] = new_id
        config["app"]["machine_code"] = machine_code
        config["app"]["user_id_created_at"] = datetime.utcnow().isoformat()
        
        self.save_config(config)
        
        return UserIdInfo(
            user_id=new_id,
            machine_code=machine_code,
            created_at=datetime.utcnow(),
            source="generated",
        )
    
    def set_user_id(self, user_id: str) -> UserIdInfo:
        """Set a specific user-id.
        
        Used for machine migration or manual override.
        
        Args:
            user_id: User-id to set
            
        Returns:
            UserIdInfo with the new user-id
        """
        # Validate format
        sanitized = self._sanitize_id(user_id)
        
        config = self.load_config()
        if "app" not in config:
            config["app"] = {}
        
        config["app"]["user_id"] = sanitized
        config["app"]["user_id_set_at"] = datetime.utcnow().isoformat()
        
        self.save_config(config)
        
        return UserIdInfo(
            user_id=sanitized,
            source="config",
        )
    
    def validate_user_id(self, user_id: str) -> bool:
        """Validate user-id format.
        
        Args:
            user_id: User-id to validate
            
        Returns:
            True if valid
        """
        return bool(self.USER_ID_PATTERN.match(user_id))


# Global user-id manager instance
_user_id_manager: UserIdManager | None = None


def get_user_id_manager() -> UserIdManager:
    """Get the global user-id manager instance.
    
    Returns:
        Global UserIdManager instance
    """
    global _user_id_manager
    if _user_id_manager is None:
        _user_id_manager = UserIdManager()
    return _user_id_manager