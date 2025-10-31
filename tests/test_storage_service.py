"""
Tests for the unified StorageService implementation.
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from aisignal.core.models import Resource, UserContext
from aisignal.core.services.storage_service import StorageService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def storage_service(temp_db):
    """Create a StorageService instance with a temporary database."""
    return StorageService(temp_db)


@pytest.fixture
def user_context():
    """Create a test user context."""
    return UserContext(user_id="test_user")


@pytest.fixture
def sample_resources(user_context):
    """Create sample resources for testing."""
    return [
        Resource(
            id="placeholder_1",  # Will be replaced by generated ID
            user_id=user_context.user_id,
            title="Test Resource 1",
            url="https://example.com/resource1",
            categories=["tech", "ai"],
            ranking=8.5,
            summary="A test resource about AI technology",
            full_content="This is the full content of resource 1",
            datetime=datetime.now(),
            source="https://example.com/feed",
            notes="Test notes",
        ),
        Resource(
            id="placeholder_2",  # Will be replaced by generated ID
            user_id=user_context.user_id,
            title="Test Resource 2",
            url="https://example.com/resource2",
            categories=["tech", "web"],
            ranking=7.2,
            summary="A test resource about web technology",
            full_content="This is the full content of resource 2",
            datetime=datetime.now(),
            source="https://example.com/feed",
        ),
    ]


class TestStorageService:
    """Test cases for StorageService."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_resources(
        self, storage_service, user_context, sample_resources
    ):
        """Test storing and retrieving resources."""
        # Store resources
        result = await storage_service.store_resources(user_context, sample_resources)
        assert result.is_success
        assert result.data == 2

        # Retrieve all resources
        resources = await storage_service.get_resources(user_context)
        assert len(resources) == 2

        # Check resource details - use generated IDs
        resource_1 = next((r for r in resources if r.title == "Test Resource 1"), None)
        assert resource_1 is not None
        assert resource_1.title == "Test Resource 1"
        assert resource_1.categories == ["tech", "ai"]
        assert resource_1.ranking == 8.5

    @pytest.mark.asyncio
    async def test_get_resource_by_id(
        self, storage_service, user_context, sample_resources
    ):
        """Test retrieving a specific resource by ID."""
        # Store resources first
        await storage_service.store_resources(user_context, sample_resources)

        # Get all resources to find the generated ID
        all_resources = await storage_service.get_resources(user_context)
        resource_1 = next(
            (r for r in all_resources if r.title == "Test Resource 1"), None
        )
        assert resource_1 is not None

        # Get specific resource by generated ID
        resource = await storage_service.get_resource_by_id(user_context, resource_1.id)
        assert resource is not None
        assert resource.title == "Test Resource 1"
        assert resource.id == resource_1.id

        # Test non-existent resource
        resource = await storage_service.get_resource_by_id(
            user_context, "non_existent"
        )
        assert resource is None

    @pytest.mark.asyncio
    async def test_filter_resources_by_categories(
        self, storage_service, user_context, sample_resources
    ):
        """Test filtering resources by categories."""
        # Store resources first
        await storage_service.store_resources(user_context, sample_resources)

        # Filter by "ai" category
        resources = await storage_service.get_resources(user_context, categories={"ai"})
        assert len(resources) == 1
        assert resources[0].title == "Test Resource 1"

        # Filter by "web" category
        resources = await storage_service.get_resources(
            user_context, categories={"web"}
        )
        assert len(resources) == 1
        assert resources[0].title == "Test Resource 2"

        # Filter by "tech" category (should return both)
        resources = await storage_service.get_resources(
            user_context, categories={"tech"}
        )
        assert len(resources) == 2

    @pytest.mark.asyncio
    async def test_filter_resources_by_sources(
        self, storage_service, user_context, sample_resources
    ):
        """Test filtering resources by sources."""
        # Store resources first
        await storage_service.store_resources(user_context, sample_resources)

        # Filter by source
        resources = await storage_service.get_resources(
            user_context, sources={"https://example.com/feed"}
        )
        assert len(resources) == 2

        # Filter by non-existent source
        resources = await storage_service.get_resources(
            user_context, sources={"https://nonexistent.com/feed"}
        )
        assert len(resources) == 0

    @pytest.mark.asyncio
    async def test_update_resource(
        self, storage_service, user_context, sample_resources
    ):
        """Test updating resource data."""
        # Store resources first
        await storage_service.store_resources(user_context, sample_resources)

        # Get the generated ID for the first resource
        all_resources = await storage_service.get_resources(user_context)
        resource_1 = next(
            (r for r in all_resources if r.title == "Test Resource 1"), None
        )
        assert resource_1 is not None

        # Update resource
        updates = {
            "title": "Updated Title",
            "summary": "Updated summary",
            "ranking": 9.0,
            "categories": ["updated", "category"],
        }

        result = await storage_service.update_resource(
            user_context, resource_1.id, updates
        )
        assert result.is_success

        # Verify update
        resource = await storage_service.get_resource_by_id(user_context, resource_1.id)
        assert resource.title == "Updated Title"
        assert resource.summary == "Updated summary"
        assert resource.ranking == 9.0
        assert resource.categories == ["updated", "category"]

    @pytest.mark.asyncio
    async def test_mark_resource_removed(
        self, storage_service, user_context, sample_resources
    ):
        """Test soft deletion of resources."""
        # Store resources first
        await storage_service.store_resources(user_context, sample_resources)

        # Get the generated ID for the first resource
        all_resources = await storage_service.get_resources(user_context)
        resource_1 = next(
            (r for r in all_resources if r.title == "Test Resource 1"), None
        )
        resource_2 = next(
            (r for r in all_resources if r.title == "Test Resource 2"), None
        )
        assert resource_1 is not None
        assert resource_2 is not None

        # Mark resource as removed
        result = await storage_service.mark_resource_removed(
            user_context, resource_1.id
        )
        assert result.is_success

        # Verify resource is not returned in normal queries
        resources = await storage_service.get_resources(user_context)
        assert len(resources) == 1
        assert resources[0].title == "Test Resource 2"

        # Verify resource cannot be retrieved by ID
        resource = await storage_service.get_resource_by_id(user_context, resource_1.id)
        assert resource is None

    @pytest.mark.asyncio
    async def test_source_content_operations(self, storage_service, user_context):
        """Test storing and retrieving source content."""
        url = "https://example.com/source"
        content = "# Test Content\n\nThis is test markdown content."

        # Store content
        result = await storage_service.store_source_content(user_context, url, content)
        assert result.is_success

        # Retrieve content
        retrieved_content = await storage_service.get_sources_content(user_context, url)
        assert retrieved_content == content

        # Test non-existent content
        missing_content = await storage_service.get_sources_content(
            user_context, "https://nonexistent.com"
        )
        assert missing_content is None

    @pytest.mark.asyncio
    async def test_get_user_statistics(
        self, storage_service, user_context, sample_resources
    ):
        """Test getting user statistics."""
        # Initially empty
        stats = await storage_service.get_user_statistics(user_context)
        assert stats["total_resources"] == 0
        assert stats["user_id"] == user_context.user_id

        # Store resources and source content
        await storage_service.store_resources(user_context, sample_resources)
        await storage_service.store_source_content(
            user_context, "https://example.com/feed", "Test content"
        )

        # Check updated statistics
        stats = await storage_service.get_user_statistics(user_context)
        assert stats["total_resources"] == 2
        assert stats["total_sources"] == 1
        assert stats["total_source_content"] == 1
        assert stats["user_id"] == user_context.user_id

    @pytest.mark.asyncio
    async def test_sorting_and_pagination(self, storage_service, user_context):
        """Test resource sorting and pagination."""
        # Create resources with different rankings and dates
        resources = []
        for i in range(5):
            resource = Resource(
                id=f"resource_{i}",
                user_id=user_context.user_id,
                title=f"Resource {i}",
                url=f"https://example.com/resource{i}",
                categories=["test"],
                ranking=float(i),  # 0, 1, 2, 3, 4
                summary=f"Summary {i}",
                full_content=f"Content {i}",
                datetime=datetime.now(),
                source="https://example.com/feed",
            )
            resources.append(resource)

        await storage_service.store_resources(user_context, resources)

        # Test sorting by ranking (descending by default)
        sorted_resources = await storage_service.get_resources(
            user_context, sort_by="ranking", sort_desc=True
        )
        assert len(sorted_resources) == 5
        assert sorted_resources[0].ranking == 4.0
        assert sorted_resources[-1].ranking == 0.0

        # Test pagination
        paginated_resources = await storage_service.get_resources(
            user_context, limit=2, offset=1
        )
        assert len(paginated_resources) == 2

    @pytest.mark.asyncio
    async def test_error_handling(self, storage_service, user_context):
        """Test error handling in various scenarios."""
        # Test updating non-existent resource
        result = await storage_service.update_resource(
            user_context, "non_existent", {"title": "New Title"}
        )
        assert result.is_error
        assert result.status.value == "not_found"

        # Test removing non-existent resource (should still succeed gracefully)
        result = await storage_service.mark_resource_removed(
            user_context, "non_existent"
        )
        # This should still return success as the operation is idempotent
        assert result.is_success

    def test_schema_updates(self, temp_db):
        """Test that schema updates are applied correctly."""
        # Create a storage service which should apply schema updates
        _ = StorageService(temp_db)

        # Check that required columns exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(items)")
            columns = [column[1] for column in cursor.fetchall()]

            assert "removed" in columns
            assert "notes" in columns
