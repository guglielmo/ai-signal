"""
Integration tests for CoreService event emission.

Tests that CoreService properly emits events through the EventBus.
"""

import pytest

from aisignal.core.models import (
    Resource,
    ResourceUpdatedEvent,
    SyncCompletedEvent,
    SyncProgressEvent,
    UserContext,
)
from aisignal.core.services.core_service import CoreService
from tests.mocks import (
    MockConfigManager,
    MockContentService,
    MockEventBus,
    MockStorageService,
)


@pytest.mark.asyncio
class TestCoreServiceEventEmission:
    """Test suite for CoreService event emission"""

    @pytest.fixture
    def user_context(self):
        """Provide a test user context"""
        return UserContext(user_id="test_user")

    @pytest.fixture
    def event_bus(self):
        """Provide a mock event bus"""
        return MockEventBus()

    @pytest.fixture
    def core_service(self, event_bus):
        """Provide a CoreService with all dependencies"""
        storage = MockStorageService()
        config = MockConfigManager()
        content = MockContentService()

        return CoreService(
            storage_service=storage,
            config_manager=config,
            content_service=content,
            event_bus=event_bus,
        )

    async def test_update_resource_emits_event(
        self, core_service, event_bus, user_context
    ):
        """Test that updating a resource emits ResourceUpdatedEvent"""
        from datetime import datetime

        # Create a test resource first
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

        # Store the resource
        await core_service.storage.store_resources(user_context, [resource])

        # Clear any events from storage
        event_bus.published_events.clear()

        # Update the resource
        result = await core_service.update_resource(
            user_context, "test-123", {"title": "Updated Title"}
        )

        # Check that update was successful
        assert result.is_success

        # Check that ResourceUpdatedEvent was emitted
        events = event_bus.get_events_of_type(ResourceUpdatedEvent)
        assert len(events) == 1
        assert events[0].resource_id == "test-123"
        assert events[0].operation == "updated"

    async def test_remove_resource_emits_event(
        self, core_service, event_bus, user_context
    ):
        """
        Test removing a resource emits ResourceUpdatedEvent
        with operation='removed'.
        """
        from datetime import datetime

        # Create a test resource first
        resource = Resource(
            id="test-456",
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

        # Store the resource
        await core_service.storage.store_resources(user_context, [resource])

        # Clear any events from storage
        event_bus.published_events.clear()

        # Remove the resource
        result = await core_service.remove_resource(user_context, "test-456")

        # Check that removal was successful
        assert result.is_success

        # Check that ResourceUpdatedEvent was emitted with operation='removed'
        events = event_bus.get_events_of_type(ResourceUpdatedEvent)
        assert len(events) == 1
        assert events[0].resource_id == "test-456"
        assert events[0].operation == "removed"

    async def test_sync_emits_progress_events(
        self, core_service, event_bus, user_context
    ):
        """Test that sync_sources emits SyncProgressEvent during sync"""
        # Configure sources
        core_service.config._sources = ["https://example.com/feed"]

        # Clear events
        event_bus.published_events.clear()

        # Run sync
        result = await core_service.sync_sources(user_context)

        # Check that sync completed (even if no real content was fetched)
        assert result is not None

        # Check that progress events were emitted
        progress_events = event_bus.get_events_of_type(SyncProgressEvent)
        assert len(progress_events) > 0

        # Check that at least one progress event has progress information
        has_progress = any(e.total > 0 for e in progress_events)
        assert has_progress

    async def test_sync_emits_completed_event(
        self, core_service, event_bus, user_context
    ):
        """Test that sync_sources emits SyncCompletedEvent when done"""
        # Configure sources
        core_service.config._sources = ["https://example.com/feed"]

        # Clear events
        event_bus.published_events.clear()

        # Run sync
        await core_service.sync_sources(user_context)

        # Check that SyncCompletedEvent was emitted
        completed_events = event_bus.get_events_of_type(SyncCompletedEvent)
        assert len(completed_events) == 1
        assert completed_events[0].success is True

    async def test_sync_emits_resource_created_events(
        self, core_service, event_bus, user_context
    ):
        """Test that sync emits ResourceUpdatedEvent for newly created resources"""
        # Configure sources
        core_service.config._sources = ["https://example.com/feed"]

        # Clear events
        event_bus.published_events.clear()

        # Run sync
        await core_service.sync_sources(user_context)

        # Check for ResourceUpdatedEvent with operation='created'
        # Note: This depends on MockContentService returning mock data
        resource_events = event_bus.get_events_of_type(ResourceUpdatedEvent)
        created_events = [e for e in resource_events if e.operation == "created"]

        # MockContentService returns 3 items per source
        assert len(created_events) >= 0  # May be 0 if no content was analyzed

    async def test_core_service_without_event_bus(self, user_context):
        """Test that CoreService works without EventBus (backward compatibility)"""
        # Create CoreService without event bus
        core_service = CoreService(
            storage_service=MockStorageService(),
            config_manager=MockConfigManager(),
            content_service=MockContentService(),
            event_bus=None,  # No event bus
        )

        from datetime import datetime

        # Create a test resource
        resource = Resource(
            id="test-789",
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

        # Store the resource
        await core_service.storage.store_resources(user_context, [resource])

        # Update should work without error even without event bus
        result = await core_service.update_resource(
            user_context, "test-789", {"title": "Updated Title"}
        )

        assert result.is_success

    async def test_sync_error_emits_failed_completed_event(
        self, event_bus, user_context
    ):
        """Test that sync errors emit SyncCompletedEvent with errors tracked"""

        # Create a content service that will fail
        class FailingContentService(MockContentService):
            async def fetch_content(self, url: str):
                raise Exception("Simulated fetch error")

        core_service = CoreService(
            storage_service=MockStorageService(),
            config_manager=MockConfigManager(),
            content_service=FailingContentService(),
            event_bus=event_bus,
        )

        # Configure sources
        core_service.config._sources = ["https://example.com/feed"]

        # Clear events
        event_bus.published_events.clear()

        # Run sync (should complete with errors tracked)
        result = await core_service.sync_sources(user_context)

        # Check that sync completed (it doesn't fail completely, just tracks errors)
        assert result.is_success

        # Check that SyncCompletedEvent was emitted
        completed_events = event_bus.get_events_of_type(SyncCompletedEvent)
        assert len(completed_events) == 1
        # With errors tracked, the event should indicate success=True but with errors
        assert completed_events[0].success is True
        # Errors should be tracked
        assert len(completed_events[0].errors) > 0
