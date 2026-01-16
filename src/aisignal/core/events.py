"""
Event System for AI Signal

Provides a simple pub/sub event bus for decoupled communication
between Core services and UI components.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# Event Types
# =============================================================================


class EventType(Enum):
    """Enumeration of all event types in the system."""

    # Sync events
    SYNC_STARTED = "sync_started"
    SYNC_PROGRESS = "sync_progress"
    SYNC_COMPLETED = "sync_completed"
    SYNC_ERROR = "sync_error"

    # Resource events
    RESOURCE_ADDED = "resource_added"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_REMOVED = "resource_removed"
    RESOURCES_LOADED = "resources_loaded"

    # Content events
    CONTENT_FETCHED = "content_fetched"
    CONTENT_ANALYZED = "content_analyzed"

    # Config events
    CONFIG_CHANGED = "config_changed"


# =============================================================================
# Event Data Classes
# =============================================================================


@dataclass
class Event:
    """Base event class."""

    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncProgressEvent(Event):
    """Event for sync progress updates."""

    type: EventType = EventType.SYNC_PROGRESS
    source_url: str = ""
    phase: str = ""  # "fetching", "analyzing", "processing"
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""


@dataclass
class SyncCompletedEvent(Event):
    """Event emitted when sync completes."""

    type: EventType = EventType.SYNC_COMPLETED
    total_sources: int = 0
    processed_sources: int = 0
    new_resources: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class ResourceEvent(Event):
    """Event for resource changes."""

    resource_id: str = ""
    resource_title: str = ""


@dataclass
class ResourceAddedEvent(ResourceEvent):
    """Event emitted when a resource is added."""

    type: EventType = EventType.RESOURCE_ADDED


@dataclass
class ResourceUpdatedEvent(ResourceEvent):
    """Event emitted when a resource is updated."""

    type: EventType = EventType.RESOURCE_UPDATED
    updated_fields: List[str] = field(default_factory=list)


@dataclass
class ResourceRemovedEvent(ResourceEvent):
    """Event emitted when a resource is removed."""

    type: EventType = EventType.RESOURCE_REMOVED


@dataclass
class ResourcesLoadedEvent(Event):
    """Event emitted when resources are loaded from storage."""

    type: EventType = EventType.RESOURCES_LOADED
    count: int = 0


# =============================================================================
# Event Handler Types
# =============================================================================

# Sync handler: (event) -> None
SyncEventHandler = Callable[[Event], None]

# Async handler: (event) -> Awaitable[None]
AsyncEventHandler = Callable[[Event], Any]


# =============================================================================
# Event Bus
# =============================================================================


class EventBus:
    """
    Simple event bus for pub/sub communication.

    Supports both synchronous and asynchronous event handlers.
    Events are dispatched to all subscribed handlers for that event type.

    Example:
        bus = EventBus()

        # Subscribe to events
        def on_sync_progress(event: SyncProgressEvent):
            print(f"Sync progress: {event.progress}")

        bus.subscribe(EventType.SYNC_PROGRESS, on_sync_progress)

        # Emit events
        bus.emit(SyncProgressEvent(progress=0.5, message="Processing..."))
    """

    def __init__(self):
        """Initialize the event bus."""
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[AsyncEventHandler]] = {}
        self._all_handlers: List[Callable] = []  # Handlers for all events

    def subscribe(
        self,
        event_type: EventType,
        handler: SyncEventHandler,
    ) -> Callable[[], None]:
        """
        Subscribe a synchronous handler to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when event is emitted

        Returns:
            Unsubscribe function that can be called to remove the subscription
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type.value}")

        # Return unsubscribe function
        def unsubscribe():
            if handler in self._handlers.get(event_type, []):
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from {event_type.value}")

        return unsubscribe

    def subscribe_async(
        self,
        event_type: EventType,
        handler: AsyncEventHandler,
    ) -> Callable[[], None]:
        """
        Subscribe an asynchronous handler to an event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The async handler function to call when event is emitted

        Returns:
            Unsubscribe function
        """
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []

        self._async_handlers[event_type].append(handler)
        logger.debug(f"Subscribed async handler to {event_type.value}")

        def unsubscribe():
            if handler in self._async_handlers.get(event_type, []):
                self._async_handlers[event_type].remove(handler)

        return unsubscribe

    def subscribe_all(self, handler: SyncEventHandler) -> Callable[[], None]:
        """
        Subscribe a handler to all events.

        Args:
            handler: Handler function called for every event

        Returns:
            Unsubscribe function
        """
        self._all_handlers.append(handler)

        def unsubscribe():
            if handler in self._all_handlers:
                self._all_handlers.remove(handler)

        return unsubscribe

    def emit(self, event: Event) -> None:
        """
        Emit an event synchronously.

        Calls all subscribed sync handlers for the event type.
        Async handlers are scheduled but not awaited.

        Args:
            event: The event to emit
        """
        event_type = event.type
        logger.debug(f"Emitting event: {event_type.value}")

        # Call all-event handlers
        for handler in self._all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in all-event handler: {e}")

        # Call sync handlers
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in sync handler for {event_type.value}: {e}")

        # Schedule async handlers
        for handler in self._async_handlers.get(event_type, []):
            try:
                asyncio.create_task(handler(event))
            except RuntimeError:
                # No event loop running - skip async handlers
                logger.debug(f"Skipping async handler (no event loop)")

    async def emit_async(self, event: Event) -> None:
        """
        Emit an event asynchronously.

        Awaits all async handlers and calls sync handlers.

        Args:
            event: The event to emit
        """
        event_type = event.type
        logger.debug(f"Emitting async event: {event_type.value}")

        # Call all-event handlers
        for handler in self._all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in all-event handler: {e}")

        # Call sync handlers
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in sync handler: {e}")

        # Await async handlers
        for handler in self._async_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in async handler: {e}")

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._handlers.clear()
        self._async_handlers.clear()
        self._all_handlers.clear()

    def get_handler_count(self, event_type: EventType) -> int:
        """Get the number of handlers subscribed to an event type."""
        sync_count = len(self._handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))
        return sync_count + async_count


# =============================================================================
# Global Event Bus Instance
# =============================================================================

# Default global event bus - can be overridden via DI
_default_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Creates one if it doesn't exist.
    """
    global _default_event_bus
    if _default_event_bus is None:
        _default_event_bus = EventBus()
    return _default_event_bus


def set_event_bus(bus: EventBus) -> None:
    """
    Set the global event bus instance.

    Useful for testing or custom configurations.
    """
    global _default_event_bus
    _default_event_bus = bus
