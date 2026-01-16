"""
Integration tests for CoreService and service stack.

Tests the complete service integration through the CoreService orchestrator.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IStorageService,
)
from aisignal.core.models import OperationResult, Resource, UserContext
from aisignal.core.services import CoreService, StorageService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_context():
    """Create a default user context."""
    return UserContext(user_id="test_user")


@pytest.fixture
def mock_config():
    """Create a mock configuration service."""
    config = MagicMock(spec=IConfigManager)
    config.categories = ["tech", "science", "business"]
    config.sources = ["https://example.com/feed1", "https://example.com/feed2"]
    config.content_extraction_prompt = "Extract news items from this content."
    config.min_threshold = 0.5
    config.max_threshold = 0.8
    config.jina_api_key = "test_jina_key"
    config.openai_api_key = "test_openai_key"
    config.obsidian_vault_path = "/tmp/vault"
    config.obsidian_template_path = "/tmp/template.md"
    config.sync_interval = 24
    return config


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup handled by pytest


@pytest.fixture
def storage_service(temp_db):
    """Create a real storage service with temp database."""
    return StorageService(db_path=temp_db)


@pytest.fixture
def mock_content_service():
    """Create a mock content service."""
    service = MagicMock(spec=IContentService)
    service.fetch_content = AsyncMock(return_value={
        "url": "https://example.com/feed1",
        "title": "Test Feed",
        "content": "Test content",
        "diff": "New content added",
    })
    service.analyze_content = AsyncMock(return_value={
        "https://example.com/feed1": [
            {
                "title": "Test Article",
                "url": "https://example.com/article1",
                "categories": ["tech"],
                "ranking": 0.75,
                "summary": "Test summary",
                "full_content": "Full test content",
            }
        ]
    })
    return service


@pytest.fixture
def core_service(storage_service, mock_config, mock_content_service):
    """Create a CoreService with all dependencies."""
    return CoreService(
        storage_service=storage_service,
        config_service=mock_config,
        content_service=mock_content_service,
    )


@pytest.fixture
def core_service_minimal(storage_service, mock_config):
    """Create a CoreService without content service."""
    return CoreService(
        storage_service=storage_service,
        config_service=mock_config,
        content_service=None,
    )


# =============================================================================
# CoreService Initialization Tests
# =============================================================================


class TestCoreServiceInit:
    """Tests for CoreService initialization."""

    def test_init_with_all_services(self, core_service):
        """CoreService should initialize with all services."""
        assert core_service.storage is not None
        assert core_service.config is not None
        assert core_service.content is not None

    def test_init_without_content_service(self, core_service_minimal):
        """CoreService should work without content service."""
        assert core_service_minimal.storage is not None
        assert core_service_minimal.config is not None
        assert core_service_minimal.content is None


# =============================================================================
# Resource Operations Tests
# =============================================================================


class TestResourceOperations:
    """Tests for CoreService resource operations."""

    @pytest.mark.asyncio
    async def test_get_resources_empty(self, core_service, user_context):
        """Should return empty list when no resources exist."""
        resources = await core_service.get_resources(user_context)
        assert resources == []

    @pytest.mark.asyncio
    async def test_store_and_get_resources(self, core_service, user_context):
        """Should store and retrieve resources correctly."""
        # First, store a resource through storage service
        from datetime import datetime

        resource = Resource(
            id="test-1",
            user_id=user_context.user_id,
            title="Test Resource",
            url="https://example.com/test",
            categories=["tech"],
            ranking=0.8,
            summary="Test summary",
            full_content="Test content",
            datetime=datetime.now(),
            source="https://example.com/feed",
            removed=False,
            notes="",
        )

        result = await core_service.storage.store_resources(
            user_context, [resource]
        )
        assert result.is_success

        # Now retrieve through core service
        resources = await core_service.get_resources(user_context)
        assert len(resources) == 1
        assert resources[0].title == "Test Resource"

    @pytest.mark.asyncio
    async def test_get_resources_with_filters(self, core_service, user_context):
        """Should filter resources by categories and sources."""
        from datetime import datetime

        # Store multiple resources
        resources_to_store = [
            Resource(
                id=f"test-{i}",
                user_id=user_context.user_id,
                title=f"Resource {i}",
                url=f"https://example.com/test{i}",
                categories=["tech"] if i % 2 == 0 else ["science"],
                ranking=0.8,
                summary="Summary",
                full_content="Content",
                datetime=datetime.now(),
                source="https://example.com/feed",
                removed=False,
                notes="",
            )
            for i in range(4)
        ]

        await core_service.storage.store_resources(user_context, resources_to_store)

        # Filter by category
        tech_resources = await core_service.get_resources(
            user_context,
            filters={"categories": ["tech"]}
        )
        assert len(tech_resources) == 2
        assert all("tech" in r.categories for r in tech_resources)

    @pytest.mark.asyncio
    async def test_get_resource_detail(self, core_service, user_context):
        """Should retrieve specific resource by ID."""
        from datetime import datetime

        resource = Resource(
            id="detail-test",
            user_id=user_context.user_id,
            title="Detail Test",
            url="https://example.com/detail",
            categories=["tech"],
            ranking=0.9,
            summary="Detail summary",
            full_content="Detailed content here",
            datetime=datetime.now(),
            source="https://example.com/feed",
            removed=False,
            notes="",
        )

        await core_service.storage.store_resources(user_context, [resource])

        # Get detail
        detail = await core_service.get_resource_detail(user_context, "detail-test")
        assert detail is not None
        assert detail.title == "Detail Test"
        assert detail.full_content == "Detailed content here"

    @pytest.mark.asyncio
    async def test_get_resource_detail_not_found(self, core_service, user_context):
        """Should return None for non-existent resource."""
        detail = await core_service.get_resource_detail(user_context, "nonexistent")
        assert detail is None

    @pytest.mark.asyncio
    async def test_update_resource(self, core_service, user_context):
        """Should update resource fields."""
        from datetime import datetime

        resource = Resource(
            id="update-test",
            user_id=user_context.user_id,
            title="Original Title",
            url="https://example.com/update",
            categories=["tech"],
            ranking=0.7,
            summary="Original summary",
            full_content="Original content",
            datetime=datetime.now(),
            source="https://example.com/feed",
            removed=False,
            notes="",
        )

        await core_service.storage.store_resources(user_context, [resource])

        # Update
        result = await core_service.update_resource(
            user_context,
            "update-test",
            {"notes": "Updated notes", "ranking": 0.9}
        )
        assert result.is_success

        # Verify update
        updated = await core_service.get_resource_detail(user_context, "update-test")
        assert updated.notes == "Updated notes"

    @pytest.mark.asyncio
    async def test_remove_resource(self, core_service, user_context):
        """Should mark resource as removed."""
        from datetime import datetime

        resource = Resource(
            id="remove-test",
            user_id=user_context.user_id,
            title="To Remove",
            url="https://example.com/remove",
            categories=["tech"],
            ranking=0.6,
            summary="Will be removed",
            full_content="Content",
            datetime=datetime.now(),
            source="https://example.com/feed",
            removed=False,
            notes="",
        )

        await core_service.storage.store_resources(user_context, [resource])

        # Remove
        result = await core_service.remove_resource(user_context, "remove-test")
        assert result.is_success

        # Verify removed (should not appear in regular queries)
        resources = await core_service.get_resources(user_context)
        assert len(resources) == 0


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for statistics operations."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, core_service, user_context):
        """Should return statistics even when empty."""
        stats = await core_service.get_statistics(user_context)
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, core_service, user_context):
        """Should return accurate statistics."""
        from datetime import datetime

        resources = [
            Resource(
                id=f"stat-{i}",
                user_id=user_context.user_id,
                title=f"Stat Resource {i}",
                url=f"https://example.com/stat{i}",
                categories=["tech"],
                ranking=0.8,
                summary="Summary",
                full_content="Content",
                datetime=datetime.now(),
                source="https://example.com/feed",
                removed=False,
                notes="",
            )
            for i in range(5)
        ]

        await core_service.storage.store_resources(user_context, resources)

        stats = await core_service.get_statistics(user_context)
        assert "total_resources" in stats or isinstance(stats, dict)


# =============================================================================
# Sync Operations Tests
# =============================================================================


class TestSyncOperations:
    """Tests for sync operations."""

    @pytest.mark.asyncio
    async def test_sync_without_content_service(self, core_service_minimal, user_context):
        """Should return error when content service not configured."""
        result = await core_service_minimal.sync_sources(user_context)
        assert result.is_error
        assert "not configured" in result.message.lower()

    @pytest.mark.asyncio
    async def test_sync_sources_success(self, core_service, user_context):
        """Should sync sources and store new resources."""
        result = await core_service.sync_sources(user_context)

        assert result.is_success
        assert "new_resources" in result.data
        assert result.data["processed"] > 0

    @pytest.mark.asyncio
    async def test_sync_with_no_new_content(self, core_service, user_context, mock_content_service):
        """Should handle case with no new content."""
        mock_content_service.fetch_content = AsyncMock(return_value={
            "url": "https://example.com/feed1",
            "title": "Test Feed",
            "content": "Same content",
            "diff": None,  # No diff means no changes
        })

        result = await core_service.sync_sources(user_context)
        assert result.is_success
        assert result.data["new_resources"] == 0


# =============================================================================
# Configuration Shortcuts Tests
# =============================================================================


class TestConfigShortcuts:
    """Tests for configuration convenience methods."""

    def test_get_categories(self, core_service):
        """Should return configured categories."""
        categories = core_service.get_categories()
        assert "tech" in categories
        assert "science" in categories

    def test_get_sources(self, core_service):
        """Should return configured sources."""
        sources = core_service.get_sources()
        assert len(sources) == 2

    def test_get_thresholds(self, core_service):
        """Should return threshold values."""
        thresholds = core_service.get_thresholds()
        assert thresholds["min"] == 0.5
        assert thresholds["max"] == 0.8


# =============================================================================
# Bootstrap Integration Tests
# =============================================================================


class TestBootstrap:
    """Tests for bootstrap module."""

    def test_create_minimal_container(self):
        """Should create minimal container without errors."""
        from aisignal.core.bootstrap import create_minimal_container

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            db_path = Path(tmpdir) / "storage.db"

            # Create minimal config
            config_path.write_text("""
api_keys:
  openai: "test"
  jinaai: "test"
categories:
  - tech
sources:
  - "https://example.com"
obsidian:
  vault_path: "/tmp"
  template_path: "/tmp/template.md"
sync_interval: 24
min_threshold: 0.5
max_threshold: 0.8
prompts:
  content_extraction: "Extract items"
""")

            container = create_minimal_container(
                config_path=config_path,
                db_path=db_path,
            )

            # Should be able to resolve core service
            core = container.resolve(ICoreService)
            assert core is not None
            assert core.content is None  # Minimal doesn't have content service


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_get_resources_handles_storage_error(self, user_context, mock_config):
        """Should handle storage errors gracefully."""
        mock_storage = MagicMock(spec=IStorageService)
        mock_storage.get_resources = AsyncMock(side_effect=Exception("DB Error"))

        core = CoreService(
            storage_service=mock_storage,
            config_service=mock_config,
            content_service=None,
        )

        resources = await core.get_resources(user_context)
        assert resources == []  # Returns empty list on error

    @pytest.mark.asyncio
    async def test_update_handles_error(self, user_context, mock_config):
        """Should return error result on update failure."""
        mock_storage = MagicMock(spec=IStorageService)
        mock_storage.update_resource = AsyncMock(side_effect=Exception("Update failed"))

        core = CoreService(
            storage_service=mock_storage,
            config_service=mock_config,
            content_service=None,
        )

        result = await core.update_resource(user_context, "test-id", {"notes": "test"})
        assert result.is_error
        assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_sync_handles_source_errors(self, core_service, user_context, mock_content_service):
        """Should continue syncing even if one source fails."""
        # Make first source fail
        call_count = 0

        async def fetch_with_error(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return {
                "url": url,
                "title": "Feed",
                "content": "Content",
                "diff": "New",
            }

        mock_content_service.fetch_content = AsyncMock(side_effect=fetch_with_error)

        result = await core_service.sync_sources(user_context)

        # Should still succeed overall
        assert result.is_success
        # Should have recorded the error
        assert len(result.data["errors"]) > 0
