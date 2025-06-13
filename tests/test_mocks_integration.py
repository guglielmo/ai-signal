"""
Integration tests for the mock framework and service container
"""

import pytest

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IStorageService,
)
from aisignal.core.models import Resource


@pytest.mark.asyncio
async def test_mock_storage_service(storage_service, user_context, sample_resources):
    """Test the mock storage service functionality"""
    # Store some resources
    result = await storage_service.store_resources(user_context, sample_resources)
    assert result.is_success
    assert result.data["stored"] == len(sample_resources)

    # Retrieve resources
    retrieved = await storage_service.get_resources(user_context)
    assert len(retrieved) == len(sample_resources)
    assert retrieved[0].title == sample_resources[0].title

    # Test filtering by category
    ai_resources = await storage_service.get_resources(user_context, categories={"AI"})
    assert len(ai_resources) > 0
    assert all("AI" in r.categories for r in ai_resources)


@pytest.mark.asyncio
async def test_mock_core_service(core_service, user_context, sample_resources):
    """Test the mock core service functionality"""
    # Store resources first
    await core_service.storage.store_resources(user_context, sample_resources)

    # Get resources through core service
    resources = await core_service.get_resources(user_context)
    assert len(resources) == len(sample_resources)

    # Test resource detail
    resource_detail = await core_service.get_resource_detail(
        user_context, sample_resources[0].id
    )
    assert resource_detail is not None
    assert resource_detail.id == sample_resources[0].id


@pytest.mark.asyncio
async def test_mock_content_service(content_service):
    """Test the mock content service functionality"""
    # Test fetch content
    content = await content_service.fetch_content("https://example.com")
    assert content is not None
    assert content["url"] == "https://example.com"
    assert "title" in content

    # Test analyze content
    analysis = await content_service.analyze_content(content, "Test prompt template")
    assert "https://example.com" in analysis
    assert len(analysis["https://example.com"]) > 0


def test_mock_config_manager(config_manager):
    """Test the mock config manager functionality"""
    assert len(config_manager.categories) > 0
    assert len(config_manager.sources) > 0
    assert config_manager.min_threshold > 0
    assert config_manager.max_threshold > config_manager.min_threshold


@pytest.mark.asyncio
async def test_service_container_integration(container, user_context):
    """Test that all services work together through the container"""
    # Get services from container
    storage = container.get(IStorageService)
    core = container.get(ICoreService)
    config = container.get(IConfigManager)
    content = container.get(IContentService)

    # Verify services are properly instantiated
    assert storage is not None
    assert core is not None
    assert config is not None
    assert content is not None

    # Test basic functionality
    test_resource = Resource(
        id="test_integration",
        user_id=user_context.user_id,
        title="Integration Test Resource",
        url="https://integration.test",
        categories=["Test"],
        ranking=80.0,
        summary="Test summary",
        full_content="Test content",
        datetime=pytest.importorskip("datetime").datetime.now(),
        source="https://integration.test",
    )

    # Store through storage service
    result = await storage.store_resources(user_context, [test_resource])
    assert result.is_success

    # Retrieve through core service
    resources = await core.get_resources(user_context)
    assert len(resources) == 1
    assert resources[0].id == "test_integration"


@pytest.mark.asyncio
async def test_user_isolation(container, user_context, alternative_user_context):
    """Test that resources are properly isolated between users"""
    storage = container.get(IStorageService)

    # Create resources for different users
    user1_resource = Resource(
        id="user1_resource",
        user_id=user_context.user_id,
        title="User 1 Resource",
        url="https://user1.test",
        categories=["User1"],
        ranking=70.0,
        summary="User 1 summary",
        full_content="User 1 content",
        datetime=pytest.importorskip("datetime").datetime.now(),
        source="https://user1.test",
    )

    user2_resource = Resource(
        id="user2_resource",
        user_id=alternative_user_context.user_id,
        title="User 2 Resource",
        url="https://user2.test",
        categories=["User2"],
        ranking=75.0,
        summary="User 2 summary",
        full_content="User 2 content",
        datetime=pytest.importorskip("datetime").datetime.now(),
        source="https://user2.test",
    )

    # Store resources for each user
    await storage.store_resources(user_context, [user1_resource])
    await storage.store_resources(alternative_user_context, [user2_resource])

    # Verify user 1 only sees their resources
    user1_resources = await storage.get_resources(user_context)
    assert len(user1_resources) == 1
    assert user1_resources[0].user_id == user_context.user_id

    # Verify user 2 only sees their resources
    user2_resources = await storage.get_resources(alternative_user_context)
    assert len(user2_resources) == 1
    assert user2_resources[0].user_id == alternative_user_context.user_id


@pytest.mark.asyncio
async def test_sync_progress_mock(core_service, user_context):
    """Test the sync progress mock functionality"""
    sources = ["https://example.com", "https://test.com"]

    progress_updates = []
    async for progress in core_service.sync_sources(user_context, sources):
        progress_updates.append(progress)

    # Should have received progress updates for each source (pending + completed)
    assert len(progress_updates) >= len(sources) * 2

    # Check that we got both pending and completed statuses
    statuses = [p["status"] for p in progress_updates]
    assert "PENDING" in statuses
    assert "COMPLETED" in statuses
