"""
EventBus implementation for AI Signal Core.

Provides a pub/sub event system for loose coupling between Core services and UI layer.
"""

import asyncio
import logging
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Type

from aisignal.core.interfaces import IEventBus
from aisignal.core.models import BaseEvent

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """
    EventBus implementation using a synchronous pub/sub pattern.

    This implementation:
    - Allows multiple subscribers per event type
    - Handles errors in event handlers gracefully
    - Supports both sync and async event handlers
    - Thread-safe for concurrent operations

    Example:
        >>> from aisignal.core.models import SyncProgressEvent
        >>> event_bus = EventBus()
        >>>
        >>> # Subscribe to events
        >>> def handle_progress(event: SyncProgressEvent):
        ...     print(f"Progress: {event.percentage}%")
        >>> event_bus.subscribe(SyncProgressEvent, handle_progress)
        >>>
        >>> # Publish events
        >>> event = SyncProgressEvent(current=1, total=5, message="Processing...")
        >>> event_bus.publish(event)
        Progress: 20.0%
        >>>
        >>> # Unsubscribe when done
        >>> event_bus.unsubscribe(SyncProgressEvent, handle_progress)
    """

    def __init__(self):
        """Initialize the event bus with empty subscription lists."""
        self._subscribers: Dict[Type[BaseEvent], List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(
        self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]
    ) -> None:
        """
        Subscribe to a specific event type.

        Args:
            event_type: The type of event to subscribe to
            handler: Callback function to handle the event

        Example:
            >>> def on_sync_progress(event: SyncProgressEvent):
            ...     print(f"{event.message}: {event.percentage}%")
            >>> event_bus.subscribe(SyncProgressEvent, on_sync_progress)
        """
        with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(
        self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]
    ) -> None:
        """
        Unsubscribe from a specific event type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The callback function to remove
        """
        with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(
                    f"Unsubscribed {handler.__name__} from {event_type.__name__}"
                )

    def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to all subscribers synchronously.

        Args:
            event: The event instance to publish

        Example:
            >>> event = SyncProgressEvent(
            ...     current=3, total=10, message="Fetching sources..."
            ... )
            >>> event_bus.publish(event)  # All handlers will be called
        """
        event_type = type(event)

        # Get a copy of handlers under lock to avoid race conditions
        with self._lock:
            handlers = list(self._subscribers.get(event_type, []))

        logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} subscribers")

        for handler in handlers:
            try:
                # Call the handler synchronously
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler {handler.__name__} "
                    f"for {event_type.__name__}: {e}",
                    exc_info=True,
                )

    async def publish_async(self, event: BaseEvent) -> None:
        """
        Publish an event to all subscribers asynchronously.

        This allows async handlers to be awaited properly.

        Args:
            event: The event instance to publish
        """
        event_type = type(event)

        # Get a copy of handlers under lock to avoid race conditions
        with self._lock:
            handlers = list(self._subscribers.get(event_type, []))

        logger.debug(
            f"Publishing (async) {event_type.__name__} to {len(handlers)} subscribers"
        )

        for handler in handlers:
            try:
                # Check if handler is async
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Call sync handler in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler, event)
            except Exception as e:
                logger.error(
                    f"Error in event handler {handler.__name__} "
                    f"for {event_type.__name__}: {e}",
                    exc_info=True,
                )

    def clear_all(self) -> None:
        """
        Clear all event subscriptions.
        Useful for testing and cleanup.
        """
        with self._lock:
            self._subscribers.clear()
        logger.debug("Cleared all event subscriptions")

    def get_subscriber_count(self, event_type: Type[BaseEvent]) -> int:
        """
        Get the number of subscribers for a specific event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of subscribers
        """
        with self._lock:
            return len(self._subscribers.get(event_type, []))
