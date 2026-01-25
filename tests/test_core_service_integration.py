"""
Integration tests for CoreService.

This module tests the CoreService orchestrator with real service implementations
to ensure they work together correctly.
"""

from datetime import datetime

import pytest
import yaml

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IStorageService,
)
from aisignal.core.models import OperationStatus, Resource, UserContext
from aisignal.core.services import ConfigService, CoreService, StorageService
from aisignal.utils.advanced_service_container import ServiceContainer

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing"""
    config_data = {
        "api_keys": {
            "openai": "test-openai-key",
            "jinaai": "test-jina-key",
        },
        "categories": ["AI", "Programming", "Data Science"],
        "sources": ["https://example.com", "https://test.com"],
        "obsidian": {
            "vault_path": "/tmp/vault",
            "template_path": "/tmp/template.md",
        },
        "sync_interval": 24,
        "max_threshold": 80.0,
        "min_threshold": 50.0,
        "prompts": {
            "content_extraction": "Extract key information",
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)

    return config_file


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing"""
    db_file = tmp_path / "test.db"
    return str(db_file)


@pytest.fixture
def real_storage_service(temp_db):
    """Create a real StorageService instance"""
    return StorageService(temp_db)


@pytest.fixture
def real_config_service(temp_config_file):
    """Create a real ConfigService instance"""
    return ConfigService(temp_config_file)


@pytest.fixture
def integration_container(temp_db, temp_config_file):
    """Create a service container with real services for integration testing"""
    from tests.mocks import MockContentService

    container = ServiceContainer()

    # Use real services for storage and config
    container.register_singleton(
        IStorageService, StorageService, factory=lambda: StorageService(temp_db)
    )
    container.register_singleton(
        IConfigManager, ConfigService, factory=lambda: ConfigService(temp_config_file)
    )

    # Use mock content service to avoid external API calls in tests
    container.register_singleton(IContentService, MockContentService)

    # Register CoreService which will use all the above services
    container.register_singleton(ICoreService, CoreService)

    return container


@pytest.fixture
def user_context():
    """Standard test user context"""
    return UserContext(user_id="test_user")


@pytest.fixture
def sample_resources(user_context):
    """Sample resources for testing"""
    return [
        Resource(
            id="resource_1",
            user_id=user_context.user_id,
            title="AI Fundamentals",
            url="https://example.com/ai-fundamentals",
            categories=["AI", "Programming"],
            ranking=85.0,
            summary="A guide to AI fundamentals",
            full_content="# AI Fundamentals\n\nDetailed content...",
            datetime=datetime(2024, 1, 15, 10, 30, 0),
            source="https://example.com",
        ),
        Resource(
            id="resource_2",
            user_id=user_context.user_id,
            title="Python Advanced",
            url="https://example.com/python-advanced",
            categories=["Programming"],
            ranking=65.0,
            summary="Advanced Python techniques",
            full_content="# Advanced Python\n\nDetailed content...",
            datetime=datetime(2024, 1, 16, 14, 45, 0),
            source="https://example.com",
        ),
        Resource(
            id="resource_3",
            user_id=user_context.user_id,
            title="Data Science with Pandas",
            url="https://test.com/pandas",
            categories=["Data Science", "Programming"],
            ranking=75.0,
            summary="Using Pandas for data science",
            full_content="# Data Science\n\nDetailed content...",
            datetime=datetime(2024, 1, 17, 9, 15, 0),
            source="https://test.com",
        ),
    ]


# =============================================================================
# CoreService Instantiation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_core_service_instantiation_via_di(integration_container):
    """Test that CoreService can be instantiated via DI container"""
    core_service = integration_container.get(ICoreService)

    assert core_service is not None
    assert isinstance(core_service, CoreService)
    assert hasattr(core_service, "storage")
    assert hasattr(core_service, "config")
    assert hasattr(core_service, "content")


@pytest.mark.asyncio
async def test_core_service_dependencies_resolved(integration_container):
    """Test that all CoreService dependencies are correctly resolved"""
    core_service = integration_container.get(ICoreService)

    # Verify dependencies are resolved
    assert core_service.storage is not None
    assert core_service.config is not None
    assert core_service.content is not None

    # Verify they are the correct types
    storage_service = integration_container.get(IStorageService)
    config_service = integration_container.get(IConfigManager)
    content_service = integration_container.get(IContentService)

    assert core_service.storage is storage_service
    assert core_service.config is config_service
    assert core_service.content is content_service


# =============================================================================
# Resource Management Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_resources_empty(integration_container, user_context):
    """Test getting resources when database is empty"""
    core_service = integration_container.get(ICoreService)

    resources = await core_service.get_resources(user_context)

    assert resources == []


@pytest.mark.asyncio
async def test_get_resources_with_data(
    integration_container, user_context, sample_resources
):
    """Test getting resources after storing them"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Retrieve resources
    resources = await core_service.get_resources(user_context)

    assert len(resources) == 3
    assert all(isinstance(r, Resource) for r in resources)


@pytest.mark.asyncio
async def test_get_resources_with_filters(
    integration_container, user_context, sample_resources
):
    """Test getting resources with category and source filters"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Filter by category
    resources = await core_service.get_resources(
        user_context, filters={"categories": ["AI"]}
    )
    assert len(resources) == 1
    assert resources[0].title == "AI Fundamentals"

    # Filter by source
    resources = await core_service.get_resources(
        user_context, filters={"sources": ["https://test.com"]}
    )
    assert len(resources) == 1
    assert resources[0].title == "Data Science with Pandas"


@pytest.mark.asyncio
async def test_get_resources_with_sorting(
    integration_container, user_context, sample_resources
):
    """Test getting resources with different sorting options"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Sort by ranking (descending - default)
    resources = await core_service.get_resources(user_context, sort_by="ranking")
    assert len(resources) == 3
    assert resources[0].ranking == 85.0  # Highest ranking first
    assert resources[1].ranking == 75.0
    assert resources[2].ranking == 65.0

    # Sort by datetime (descending)
    # Note: Storage service sets first_seen to current time on insert,
    # so we just verify we got all resources back
    resources = await core_service.get_resources(user_context, sort_by="datetime")
    assert len(resources) == 3


@pytest.mark.asyncio
async def test_get_resources_with_pagination(
    integration_container, user_context, sample_resources
):
    """Test getting resources with pagination"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Get first page
    resources = await core_service.get_resources(user_context, limit=2, offset=0)
    assert len(resources) == 2

    # Get second page
    resources = await core_service.get_resources(user_context, limit=2, offset=2)
    assert len(resources) == 1


@pytest.mark.asyncio
async def test_get_resource_detail(
    integration_container, user_context, sample_resources
):
    """Test getting resource detail by ID"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Get all resources to find the actual ID
    resources = await core_service.get_resources(user_context)
    assert len(resources) > 0

    first_resource_id = resources[0].id

    # Get resource detail
    resource = await core_service.get_resource_detail(user_context, first_resource_id)

    assert resource is not None
    assert resource.id == first_resource_id
    assert resource.title in [
        "AI Fundamentals",
        "Python Advanced",
        "Data Science with Pandas",
    ]


@pytest.mark.asyncio
async def test_get_resource_detail_not_found(integration_container, user_context):
    """Test getting resource detail for non-existent resource"""
    core_service = integration_container.get(ICoreService)

    resource = await core_service.get_resource_detail(user_context, "nonexistent")

    assert resource is None


# =============================================================================
# Resource Update Tests
# =============================================================================


@pytest.mark.asyncio
async def test_update_resource(integration_container, user_context, sample_resources):
    """Test updating a resource"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Get all resources to find the actual ID
    resources = await core_service.get_resources(user_context)
    first_resource_id = resources[0].id

    # Update resource
    result = await core_service.update_resource(
        user_context, first_resource_id, {"title": "Updated Title", "ranking": 90.0}
    )

    assert result.is_success
    assert result.status == OperationStatus.SUCCESS

    # Verify update
    resource = await core_service.get_resource_detail(user_context, first_resource_id)
    assert resource.title == "Updated Title"
    assert resource.ranking == 90.0


@pytest.mark.asyncio
async def test_update_resource_not_found(integration_container, user_context):
    """Test updating a non-existent resource"""
    core_service = integration_container.get(ICoreService)

    result = await core_service.update_resource(
        user_context, "nonexistent", {"title": "New Title"}
    )

    assert result.is_error
    assert result.status == OperationStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_update_resource_no_updates(
    integration_container, user_context, sample_resources
):
    """Test updating a resource with no updates"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Update with no changes
    result = await core_service.update_resource(user_context, "resource_1", {})

    assert result.is_error
    assert result.status == OperationStatus.INVALID_INPUT


# =============================================================================
# Resource Removal Tests
# =============================================================================


@pytest.mark.asyncio
async def test_remove_resource(integration_container, user_context, sample_resources):
    """Test removing a resource"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    # Get all resources to find the actual ID
    resources = await core_service.get_resources(user_context)
    first_resource_id = resources[0].id

    # Remove resource
    result = await core_service.remove_resource(user_context, first_resource_id)

    assert result.is_success

    # Verify resource is removed (should not appear in get_resources)
    resources_after = await core_service.get_resources(user_context)
    assert len(resources_after) == 2
    assert not any(r.id == first_resource_id for r in resources_after)


@pytest.mark.asyncio
async def test_remove_resource_not_found(integration_container, user_context):
    """Test removing a non-existent resource"""
    core_service = integration_container.get(ICoreService)

    result = await core_service.remove_resource(user_context, "nonexistent")

    assert result.is_error
    assert result.status == OperationStatus.NOT_FOUND


# =============================================================================
# Statistics Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_statistics_empty(integration_container, user_context):
    """Test getting statistics when no resources exist"""
    core_service = integration_container.get(ICoreService)

    stats = await core_service.get_statistics(user_context)

    assert isinstance(stats, dict)
    assert stats["total_resources"] == 0


@pytest.mark.asyncio
async def test_get_statistics_with_data(
    integration_container, user_context, sample_resources
):
    """Test getting statistics with resources"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # Store sample resources
    await storage_service.store_resources(user_context, sample_resources)

    stats = await core_service.get_statistics(user_context)

    assert stats["total_resources"] == 3
    assert stats["user_id"] == user_context.user_id


# =============================================================================
# Configuration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_config_value(integration_container):
    """Test getting configuration values"""
    core_service = integration_container.get(ICoreService)

    categories = core_service.get_config_value("categories")
    sources = core_service.get_config_value("sources")

    assert categories == ["AI", "Programming", "Data Science"]
    assert sources == ["https://example.com", "https://test.com"]

    # Test invalid key raises ValueError
    with pytest.raises(ValueError, match="Configuration key 'invalid_key' not found"):
        core_service.get_config_value("invalid_key")


@pytest.mark.asyncio
async def test_update_config(integration_container, temp_config_file):
    """Test updating configuration"""
    core_service = integration_container.get(ICoreService)

    new_config = {
        "api_keys": {
            "openai": "new-openai-key",
            "jinaai": "new-jina-key",
        },
        "categories": ["ML", "AI"],
        "sources": ["https://newsite.com"],
        "obsidian": {
            "vault_path": "/new/vault",
            "template_path": "/new/template.md",
        },
        "sync_interval": 12,
        "max_threshold": 85.0,
        "min_threshold": 55.0,
        "prompts": {
            "content_extraction": "New prompt",
        },
    }

    result = await core_service.update_config(new_config)

    assert result.is_success

    # Verify config was updated
    categories = core_service.get_config_value("categories")
    assert categories == ["ML", "AI"]


# =============================================================================
# Integration with Multiple Services Tests
# =============================================================================


@pytest.mark.asyncio
async def test_full_workflow_integration(
    integration_container, user_context, sample_resources
):
    """Test a complete workflow using CoreService"""
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    # 1. Start with empty database
    resources = await core_service.get_resources(user_context)
    assert len(resources) == 0

    # 2. Store resources
    await storage_service.store_resources(user_context, sample_resources)

    # 3. Get all resources
    resources = await core_service.get_resources(user_context)
    assert len(resources) == 3

    # 4. Get filtered resources
    ai_resources = await core_service.get_resources(
        user_context, filters={"categories": ["AI"]}
    )
    assert len(ai_resources) == 1

    # Get actual IDs for later operations
    first_resource_id = resources[0].id
    second_resource_id = resources[1].id

    # 5. Update a resource
    result = await core_service.update_resource(
        user_context, first_resource_id, {"notes": "This is a great resource!"}
    )
    assert result.is_success

    # 6. Get resource detail
    resource = await core_service.get_resource_detail(user_context, first_resource_id)
    assert resource.notes == "This is a great resource!"

    # 7. Remove a resource
    result = await core_service.remove_resource(user_context, second_resource_id)
    assert result.is_success

    # 8. Verify removal
    resources_after = await core_service.get_resources(user_context)
    assert len(resources_after) == 2

    # 9. Get statistics
    stats = await core_service.get_statistics(user_context)
    assert stats["total_resources"] == 2


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Multi-user isolation will be implemented in future milestone (Issue #4)"
)
async def test_multiuser_isolation(integration_container):
    """Test that resources are isolated between users

    Note: This feature is planned for a future milestone.
    See docs/migration-issues.md Issue 4: Multi-user Data Model Preparation
    """
    core_service = integration_container.get(ICoreService)
    storage_service = integration_container.get(IStorageService)

    user1 = UserContext(user_id="user1")
    user2 = UserContext(user_id="user2")

    # Create resources for user1
    user1_resources = [
        Resource(
            id="user1_resource_1",
            user_id=user1.user_id,
            title="User 1 Resource",
            url="https://user1.com/resource",
            categories=["AI"],
            ranking=80.0,
            summary="User 1's resource",
            full_content="Content for user 1",
            datetime=datetime.now(),
            source="https://user1.com",
        )
    ]

    # Create resources for user2
    user2_resources = [
        Resource(
            id="user2_resource_1",
            user_id=user2.user_id,
            title="User 2 Resource",
            url="https://user2.com/resource",
            categories=["Programming"],
            ranking=70.0,
            summary="User 2's resource",
            full_content="Content for user 2",
            datetime=datetime.now(),
            source="https://user2.com",
        )
    ]

    # Store resources for both users
    await storage_service.store_resources(user1, user1_resources)
    await storage_service.store_resources(user2, user2_resources)

    # Verify user1 only sees their resources
    user1_results = await core_service.get_resources(user1)
    assert len(user1_results) == 1
    assert user1_results[0].user_id == "user1"

    # Verify user2 only sees their resources
    user2_results = await core_service.get_resources(user2)
    assert len(user2_results) == 1
    assert user2_results[0].user_id == "user2"


# =============================================================================
# Additional Tests for Coverage
# =============================================================================


@pytest.fixture
def real_core_service(temp_db, temp_config_file):
    """Create a real CoreService instance for coverage tests"""
    from tests.mocks import MockContentService

    storage = StorageService(temp_db)
    config = ConfigService(temp_config_file)
    content = MockContentService()

    return CoreService(
        storage_service=storage,
        config_manager=config,
        content_service=content,
        event_bus=None,  # No event bus for these tests
    )


@pytest.mark.asyncio
async def test_sync_sources_with_no_sources_configured(
    real_core_service, user_context, tmp_path
):
    """Test sync_sources when no sources are configured"""
    # Pass empty sources list explicitly (overriding config)
    result = await real_core_service.sync_sources(user_context, source_urls=[])

    # Should return invalid_input error
    assert result.status == OperationStatus.INVALID_INPUT
    assert "No sources configured" in result.message


@pytest.mark.asyncio
async def test_search_resources(real_core_service, user_context, tmp_path):
    """Test searching resources by text query"""
    # Create test resources with different titles and summaries
    resources = [
        Resource(
            id="search_test_1",
            user_id="test_user",  # Match user_context
            title="Python Programming Guide",
            url="https://example.com/python",
            categories=["Programming"],
            ranking=85.0,
            summary="Learn Python basics and advanced concepts",
            full_content="Python is a great language",
            datetime=datetime.now(),
            source="https://example.com",
        ),
        Resource(
            id="search_test_2",
            user_id="test_user",  # Match user_context
            title="JavaScript Best Practices",
            url="https://example.com/javascript",
            categories=["Programming"],
            ranking=80.0,
            summary="Master JavaScript development",
            full_content="JavaScript is versatile",
            datetime=datetime.now(),
            source="https://example.com",
        ),
        Resource(
            id="search_test_3",
            user_id="test_user",  # Match user_context
            title="Machine Learning Basics",
            url="https://example.com/ml",
            categories=["AI"],
            ranking=90.0,
            summary="Introduction to Python-based ML",
            full_content="ML with Python",
            datetime=datetime.now(),
            source="https://example.com",
        ),
    ]

    # Store resources
    storage_service = real_core_service.storage
    await storage_service.store_resources(user_context, resources)

    # Search for "Python" (should match 2 resources: title + summary)
    results = await real_core_service.search_resources(user_context, "Python")
    assert len(results) == 2
    # Check by title instead of ID since search matches content
    titles = [r.title for r in results]
    assert "Python Programming Guide" in titles
    assert "Machine Learning Basics" in titles

    # Search for "JavaScript" (should match 1 resource)
    results = await real_core_service.search_resources(user_context, "JavaScript")
    assert len(results) == 1
    assert "JavaScript" in results[0].title

    # Search with no matches
    results = await real_core_service.search_resources(user_context, "NonExistent")
    assert len(results) == 0

    # Search with filters
    results = await real_core_service.search_resources(
        user_context, "Python", filters={"categories": ["Programming"]}
    )
    assert len(results) == 1
    assert "Python Programming Guide" in results[0].title


@pytest.mark.asyncio
async def test_update_config_error_handling(real_core_service):
    """Test update_config error handling when save fails"""
    # Mock the config save method to raise an exception
    original_save = real_core_service.config.save

    def failing_save(config):
        raise Exception("Failed to save config")

    real_core_service.config.save = failing_save

    # Attempt to update config
    result = await real_core_service.update_config({"test_key": "test_value"})

    # Should return error result
    assert result.status == OperationStatus.ERROR
    assert "Failed to update configuration" in result.message

    # Restore original save method
    real_core_service.config.save = original_save


@pytest.mark.asyncio
async def test_sync_sources_with_webpage_content(real_core_service, user_context):
    """Test sync_sources with regular webpage (non-RSS) content"""
    # Configure a regular webpage URL (not RSS)
    webpage_url = "https://example.com/article"

    # Mock the content service to return webpage content
    async def mock_fetch_content(url):
        return "Test webpage content from " + url

    # Replace the fetch_content method temporarily
    original_fetch = real_core_service.content.fetch_content
    real_core_service.content.fetch_content = mock_fetch_content

    # Mock analyze_content to return analyzed items
    async def mock_analyze_content(content_list, prompt):
        return {
            webpage_url: [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article/1",
                    "categories": ["Tech"],
                    "ranking": 85.0,
                    "summary": "Test summary",
                    "full_content": "Test content",
                }
            ]
        }

    original_analyze = real_core_service.content.analyze_content
    real_core_service.content.analyze_content = mock_analyze_content

    # Run sync with the webpage URL
    result = await real_core_service.sync_sources(
        user_context, source_urls=[webpage_url]
    )

    # Verify sync was successful
    assert result.is_success
    assert result.data["sources_synced"] == 1
    assert result.data["new_items"] == 1

    # Restore original methods
    real_core_service.content.fetch_content = original_fetch
    real_core_service.content.analyze_content = original_analyze
