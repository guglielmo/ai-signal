from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar


@dataclass
class Resource:
    """Represents a curated content resource.

    Args:
        id: Unique identifier for the resource
        title: Resource title
        url: Original resource URL
        categories: List of assigned categories
        ranking: Numerical quality ranking
        summary: Brief content summary
        full_content: Full content in markdown
        datetime: Creation/fetch timestamp
        source: Source URL of the content
    """

    id: str
    user_id: str
    title: str
    url: str
    categories: List[str]
    ranking: float
    summary: str
    full_content: str
    datetime: datetime
    source: str
    removed: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for compatibility with other models."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "url": self.url,
            "categories": self.categories,
            "ranking": self.ranking,
            "summary": self.summary,
            "full_content": self.full_content,
            "datetime": self.datetime.isoformat(),
            "source": self.source,
            "removed": self.removed,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resource":
        """Create from dict for compatibility with other models."""
        # Handle datetime conversion
        dt = data.get("datetime")
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        elif dt is None:
            dt = datetime.now()

        return cls(
            id=data["id"],
            user_id=data["user_id"],
            title=data["title"],
            url=data["url"],
            categories=data["categories"],
            ranking=data["ranking"],
            summary=data["summary"],
            full_content=data.get("full_content", ""),
            datetime=dt,
            source=data["source"],
            removed=data.get("removed", False),
            notes=data.get("notes", ""),
        )


@dataclass
class UserContext:
    """Represents the context of a user for operations.

    In the current single-user implementation, this is a placeholder
    that will be expanded in the future for multi-user support.

    Args:
        user_id: Identifier for the user (defaults to "default_user")
    """

    user_id: str = "default_user"


class OperationStatus(Enum):
    """Status codes for operation results."""

    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    UNAUTHORIZED = "unauthorized"


T = TypeVar("T")


@dataclass
class OperationResult(Generic[T]):
    """Represents the result of an operation with consistent error handling.

    Args:
        status: The status of the operation
        data: The data returned by the operation (if successful)
        message: A human-readable message describing the result
        errors: A list of error details (if any)
    """

    status: OperationStatus
    data: Optional[T] = None
    message: str = ""
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def success(
        cls, data: Optional[T] = None, message: str = "Operation successful"
    ) -> "OperationResult[T]":
        """Create a success result."""
        return cls(status=OperationStatus.SUCCESS, data=data, message=message)

    @classmethod
    def error(
        cls, message: str, errors: List[Dict[str, Any]] = None
    ) -> "OperationResult[T]":
        """Create an error result."""
        return cls(status=OperationStatus.ERROR, message=message, errors=errors or [])

    @classmethod
    def not_found(cls, message: str = "Resource not found") -> "OperationResult[T]":
        """Create a not found result."""
        return cls(status=OperationStatus.NOT_FOUND, message=message)

    @classmethod
    def invalid_input(
        cls, message: str, errors: List[Dict[str, Any]] = None
    ) -> "OperationResult[T]":
        """Create an invalid input result."""
        return cls(
            status=OperationStatus.INVALID_INPUT, message=message, errors=errors or []
        )

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.status == OperationStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the operation resulted in an error."""
        return not self.is_success


# =============================================================================
# EVENT TYPES FOR EVENT BUS
# =============================================================================


@dataclass
class BaseEvent:
    """Base class for all events in the event bus system.

    Args:
        timestamp: When the event occurred
        user_context: User context for the event
    """

    timestamp: datetime = field(default_factory=datetime.now)
    user_context: Optional[UserContext] = None


@dataclass
class SyncProgressEvent(BaseEvent):
    """Event emitted during sync operations to report progress.

    Args:
        current: Current progress value (e.g., items processed)
        total: Total items to process
        message: Human-readable progress message
        percentage: Progress as percentage (0-100)
    """

    current: int = 0
    total: int = 0
    message: str = ""

    @property
    def percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100


@dataclass
class ResourceUpdatedEvent(BaseEvent):
    """Event emitted when a resource is created, updated, or removed.

    Args:
        resource_id: ID of the affected resource
        operation: Type of operation ('created', 'updated', 'removed')
        resource: The full resource object (optional)
    """

    resource_id: str = ""
    operation: str = "updated"  # 'created', 'updated', 'removed'
    resource: Optional[Resource] = None


@dataclass
class SyncCompletedEvent(BaseEvent):
    """Event emitted when a sync operation completes.

    Args:
        success: Whether sync completed successfully
        total_resources: Total number of resources processed
        new_resources: Number of new resources added
        updated_resources: Number of resources updated
        errors: List of errors encountered (if any)
        message: Summary message
    """

    success: bool = True
    total_resources: int = 0
    new_resources: int = 0
    updated_resources: int = 0
    errors: List[str] = field(default_factory=list)
    message: str = ""


# Type alias for event handler callbacks
EventHandler = Callable[[BaseEvent], None]
