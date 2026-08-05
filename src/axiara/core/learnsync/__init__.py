"""Multi-user learning data sync (hub model).

Implements the hub-and-spoke sync model from docs/learn-sync.md:
- User identity management (stable user-id)
- Upload flow (bundle export → push to user/<user-id> branch)
- Central review flow (ingest → compare → propose → admin confirm → apply)
- Dynamic scale monitoring (D-SK10)
- Inactive-branch archiving (D-SK11)

Reuses storage layer (core/storage/) and PermissionManager.
"""

from axiara.core.learnsync.user_id import (
    UserIdManager,
    get_user_id_manager,
)
from axiara.core.learnsync.bundle import (
    BundleExporter,
    BundleValidator,
    BundleMetadata,
)
from axiara.core.learnsync.upload import (
    UploadManager,
    UploadResult,
)
from axiara.core.learnsync.review import (
    ReviewManager,
    Proposal,
    ProposalType,
)
from axiara.core.learnsync.monitor import (
    ScaleMonitor,
    ScaleTier,
    ScaleMetrics,
)
from axiara.core.learnsync.archive import (
    ArchiveManager,
    ArchiveCandidate,
)

__all__ = [
    # User identity
    "UserIdManager",
    "get_user_id_manager",
    # Bundle
    "BundleExporter",
    "BundleValidator",
    "BundleMetadata",
    # Upload
    "UploadManager",
    "UploadResult",
    # Review
    "ReviewManager",
    "Proposal",
    "ProposalType",
    # Monitor
    "ScaleMonitor",
    "ScaleTier",
    "ScaleMetrics",
    # Archive
    "ArchiveManager",
    "ArchiveCandidate",
]