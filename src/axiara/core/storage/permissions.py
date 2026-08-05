"""Permission enforcement for data layer access.

Implements defense-in-depth security for the three-layer data model:
- MAIN: Official price baseline — manual edit ONLY
- LEARN: AI-learned reference
- MARKET: Crawled market prices (with confirmation)

This module provides a PermissionManager that enforces write permissions
at the storage layer, ensuring agents cannot write to restricted layers.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class DataLayer(StrEnum):
    """The three data layers plus user uploads."""

    MAIN = "main"  # official price baseline — manual edit ONLY
    LEARN = "learn"  # AI-learned reference
    MARKET = "market"  # crawled market prices
    UPLOADS = "uploads"  # user-provided tables/documents


class PermissionError(Exception):
    """Raised when a write operation violates permission rules."""

    def __init__(self, layer: DataLayer, operation: str, reason: str) -> None:
        self.layer = layer
        self.operation = operation
        self.reason = reason
        super().__init__(f"Permission denied for {operation} on {layer.value}: {reason}")


class PermissionManager:
    """Manages write permissions for data layers.

    Permission rules (per AGENTS.md and docs/business-modes.md):
    - MAIN: Human-only. All programmatic writes are REJECTED.
    - LEARN: Allowed for AI learning skills (e.g., csv-data-import learning path).
    - MARKET: Allowed for crawler after user confirmation.
    - UPLOADS: Allowed for user-provided files.

    The caller must provide context:
    - source: "manual" | "crawler" | "learning" | "import"
    - user_confirmed: bool (required for MARKET writes from crawler)
    """

    # Define which sources can write to which layers
    LAYER_PERMISSIONS: dict[DataLayer, dict[str, bool]] = {
        DataLayer.MAIN: {
            "manual": True,      # Only manual edits allowed
            "crawler": False,    # Crawler cannot write to MAIN
            "learning": False,   # Learning cannot write to MAIN
            "import": False,     # Import cannot write to MAIN
        },
        DataLayer.LEARN: {
            "manual": True,
            "crawler": False,
            "learning": True,    # Learning skills can write
            "import": True,      # Import learning path
        },
        DataLayer.MARKET: {
            "manual": True,
            "crawler": True,     # Crawler can write after confirmation
            "learning": False,
            "import": False,
        },
        DataLayer.UPLOADS: {
            "manual": True,
            "crawler": False,
            "learning": False,
            "import": True,      # User uploads allowed
        },
    }

    # Layers that require user confirmation before write
    CONFIRMATION_REQUIRED: set[DataLayer] = {
        DataLayer.MARKET,  # Crawler writes require confirmation
    }

    def __init__(self) -> None:
        """Initialize the permission manager."""
        pass

    def check_write_permission(
        self,
        layer: DataLayer,
        source: str = "manual",
        user_confirmed: bool = False,
    ) -> bool:
        """Check if a write operation is permitted.

        Args:
            layer: Target data layer
            source: Source of the write operation
            user_confirmed: Whether user has confirmed the write

        Returns:
            True if write is permitted

        Raises:
            PermissionError: If write is not permitted
        """
        # Get permissions for this layer
        layer_perms = self.LAYER_PERMISSIONS.get(layer)
        if layer_perms is None:
            raise PermissionError(
                layer, "write", f"Unknown data layer: {layer.value}"
            )

        # Check if this source can write to this layer
        if not layer_perms.get(source, False):
            raise PermissionError(
                layer,
                "write",
                f"Source '{source}' is not allowed to write to {layer.value}",
            )

        # Check if user confirmation is required
        if layer in self.CONFIRMATION_REQUIRED and source == "crawler":
            if not user_confirmed:
                raise PermissionError(
                    layer,
                    "write",
                    f"User confirmation required for crawler writes to {layer.value}",
                )

        return True

    def check_delete_permission(
        self,
        layer: DataLayer,
        source: str = "manual",
        user_confirmed: bool = False,
    ) -> bool:
        """Check if a delete operation is permitted.

        Args:
            layer: Target data layer
            source: Source of the delete operation
            user_confirmed: Whether user has confirmed the delete

        Returns:
            True if delete is permitted

        Raises:
            PermissionError: If delete is not permitted
        """
        # Delete permissions follow same rules as write
        return self.check_write_permission(layer, source, user_confirmed)

    def can_read(self, layer: DataLayer) -> bool:
        """Check if a layer is readable.

        All layers are readable by all agents (per business-modes.md).

        Args:
            layer: Target data layer

        Returns:
            Always True (all layers readable)
        """
        return True

    def get_allowed_sources(self, layer: DataLayer) -> list[str]:
        """Get list of sources allowed to write to a layer.

        Args:
            layer: Target data layer

        Returns:
            List of allowed source identifiers
        """
        layer_perms = self.LAYER_PERMISSIONS.get(layer, {})
        return [source for source, allowed in layer_perms.items() if allowed]

    def requires_confirmation(self, layer: DataLayer, source: str) -> bool:
        """Check if a write operation requires user confirmation.

        Args:
            layer: Target data layer
            source: Source of the operation

        Returns:
            True if confirmation is required
        """
        return layer in self.CONFIRMATION_REQUIRED and source == "crawler"


# Global permission manager instance
_permission_manager: PermissionManager | None = None


def get_permission_manager() -> PermissionManager:
    """Get the global permission manager instance.

    Returns:
        Global PermissionManager instance
    """
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager
