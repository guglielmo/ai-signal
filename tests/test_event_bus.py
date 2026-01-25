"""
Tests for the EventBus implementation.

This module tests the pub/sub event system for Core-UI communication.
"""

import pytest

from aisignal.core.models import (
    BaseEvent,
    ResourceUpdatedEvent,
    SyncCompletedEvent,
    SyncProgressEvent,
    UserContext,
)
from aisignal.core.services.event_bus import EventBus


class TestEventBus:
    """Test suite for EventBus implementation"""

    @pytest.fixture
    def event_bus(self):
        """Provide a fresh EventBus instance for each test"""
        return EventBus()

    @pytest.fixture
    def user_context(self):
        """Provide a test user context"""
        return UserContext(user_id="test_user")

    def test_subscribe_and_publish(self, event_bus):
        """Test basic subscribe and publish functionality"""
        events_received = []

        def handler(event: BaseEvent):
            events_received.append(event)

        # Subscribe to SyncProgressEvent
        event_bus.subscribe(SyncProgressEvent, handler)

        # Publish an event
        event = SyncProgressEvent(current=5, total=10, message="Testing")
        event_bus.publish(event)

        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0] == event
        assert events_received[0].current == 5
        assert events_received[0].total == 10

    def test_multiple_subscribers(self, event_bus):
        """Test that multiple subscribers receive the same event"""
        handler1_events = []
        handler2_events = []

        def handler1(event: BaseEvent):
            handler1_events.append(event)

        def handler2(event: BaseEvent):
            handler2_events.append(event)

        # Subscribe both handlers
        event_bus.subscribe(SyncProgressEvent, handler1)
        event_bus.subscribe(SyncProgressEvent, handler2)

        # Publish an event
        event = SyncProgressEvent(current=3, total=10)
        event_bus.publish(event)

        # Both handlers should receive the event
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
        assert handler1_events[0] == event
        assert handler2_events[0] == event

    def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events"""
        events_received = []

        def handler(event: BaseEvent):
            events_received.append(event)

        # Subscribe and publish
        event_bus.subscribe(SyncProgressEvent, handler)
        event_bus.publish(SyncProgressEvent(current=1, total=10))
        assert len(events_received) == 1

        # Unsubscribe and publish again
        event_bus.unsubscribe(SyncProgressEvent, handler)
        event_bus.publish(SyncProgressEvent(current=2, total=10))

        # Should still have only one event
        assert len(events_received) == 1

    def test_event_type_filtering(self, event_bus):
        """Test that subscribers only receive events of subscribed type"""
        progress_events = []
        completed_events = []

        def progress_handler(event: BaseEvent):
            progress_events.append(event)

        def completed_handler(event: BaseEvent):
            completed_events.append(event)

        # Subscribe to different event types
        event_bus.subscribe(SyncProgressEvent, progress_handler)
        event_bus.subscribe(SyncCompletedEvent, completed_handler)

        # Publish both types of events
        event_bus.publish(SyncProgressEvent(current=5, total=10))
        event_bus.publish(SyncCompletedEvent(success=True, total_resources=10))

        # Each handler should only receive events of their subscribed type
        assert len(progress_events) == 1
        assert len(completed_events) == 1
        assert isinstance(progress_events[0], SyncProgressEvent)
        assert isinstance(completed_events[0], SyncCompletedEvent)

    def test_clear_all(self, event_bus):
        """Test clearing all subscriptions"""
        events_received = []

        def handler(event: BaseEvent):
            events_received.append(event)

        # Subscribe and verify it works
        event_bus.subscribe(SyncProgressEvent, handler)
        event_bus.publish(SyncProgressEvent(current=1, total=10))
        assert len(events_received) == 1

        # Clear all subscriptions
        event_bus.clear_all()

        # Publish again - should not receive events
        event_bus.publish(SyncProgressEvent(current=2, total=10))
        assert len(events_received) == 1  # Still only one

    def test_sync_progress_event_percentage(self, user_context):
        """Test SyncProgressEvent percentage calculation"""
        event = SyncProgressEvent(
            user_context=user_context, current=25, total=100, message="Testing"
        )

        assert event.percentage == 25.0

        # Test with zero total
        event_zero = SyncProgressEvent(current=5, total=0)
        assert event_zero.percentage == 0.0

    def test_resource_updated_event(self, user_context):
        """Test ResourceUpdatedEvent creation"""
        from datetime import datetime

        from aisignal.core.models import Resource

        resource = Resource(
            id="test-123",
            user_id="test_user",
            title="Test Resource",
            url="https://example.com",
            categories=["tech"],
            ranking=8.5,
            summary="Test summary",
            full_content="Test content",
            datetime=datetime.now(),
            source="https://source.com",
        )

        event = ResourceUpdatedEvent(
            user_context=user_context,
            resource_id="test-123",
            operation="updated",
            resource=resource,
        )

        assert event.resource_id == "test-123"
        assert event.operation == "updated"
        assert event.resource == resource

    def test_sync_completed_event(self, user_context):
        """Test SyncCompletedEvent creation"""
        event = SyncCompletedEvent(
            user_context=user_context,
            success=True,
            total_resources=100,
            new_resources=25,
            updated_resources=5,
            errors=[],
            message="Sync completed successfully",
        )

        assert event.success is True
        assert event.total_resources == 100
        assert event.new_resources == 25
        assert event.updated_resources == 5
        assert len(event.errors) == 0

    def test_error_in_handler_does_not_break_other_handlers(self, event_bus):
        """
        Test that an error in one handler doesn't prevent
        other handlers from running.
        """
        handler1_called = []
        handler3_called = []

        def handler1(event: BaseEvent):
            handler1_called.append(event)

        def handler2_failing(event: BaseEvent):
            raise ValueError("Handler 2 error")

        def handler3(event: BaseEvent):
            handler3_called.append(event)

        # Subscribe all handlers
        event_bus.subscribe(SyncProgressEvent, handler1)
        event_bus.subscribe(SyncProgressEvent, handler2_failing)
        event_bus.subscribe(SyncProgressEvent, handler3)

        # Publish event
        event = SyncProgressEvent(current=5, total=10)
        event_bus.publish(event)

        # Handler 1 and 3 should still be called despite handler 2 failing
        assert len(handler1_called) == 1
        assert len(handler3_called) == 1

    def test_get_subscriber_count(self, event_bus):
        """Test getting subscriber count for event types"""
        assert event_bus.get_subscriber_count(SyncProgressEvent) == 0

        def handler1(event: BaseEvent):
            pass

        def handler2(event: BaseEvent):
            pass

        event_bus.subscribe(SyncProgressEvent, handler1)
        assert event_bus.get_subscriber_count(SyncProgressEvent) == 1

        event_bus.subscribe(SyncProgressEvent, handler2)
        assert event_bus.get_subscriber_count(SyncProgressEvent) == 2

        event_bus.unsubscribe(SyncProgressEvent, handler1)
        assert event_bus.get_subscriber_count(SyncProgressEvent) == 1

    def test_duplicate_subscription(self, event_bus):
        """Test that subscribing the same handler twice doesn't duplicate events"""
        events_received = []

        def handler(event: BaseEvent):
            events_received.append(event)

        # Subscribe the same handler twice
        event_bus.subscribe(SyncProgressEvent, handler)
        event_bus.subscribe(SyncProgressEvent, handler)

        # Publish event
        event_bus.publish(SyncProgressEvent(current=5, total=10))

        # Should only receive one event
        assert len(events_received) == 1


@pytest.mark.asyncio
class TestEventBusAsync:
    """Test async functionality of EventBus"""

    @pytest.fixture
    def event_bus(self):
        """Provide a fresh EventBus instance for each test"""
        return EventBus()

    async def test_publish_async_with_sync_handler(self, event_bus):
        """Test async publish with synchronous handler"""
        events_received = []

        def sync_handler(event: BaseEvent):
            events_received.append(event)

        event_bus.subscribe(SyncProgressEvent, sync_handler)

        # Publish async
        event = SyncProgressEvent(current=5, total=10)
        await event_bus.publish_async(event)

        assert len(events_received) == 1
        assert events_received[0] == event

    async def test_publish_async_with_async_handler(self, event_bus):
        """Test async publish with async handler"""
        events_received = []

        async def async_handler(event: BaseEvent):
            events_received.append(event)

        event_bus.subscribe(SyncProgressEvent, async_handler)

        # Publish async
        event = SyncProgressEvent(current=5, total=10)
        await event_bus.publish_async(event)

        assert len(events_received) == 1
        assert events_received[0] == event
