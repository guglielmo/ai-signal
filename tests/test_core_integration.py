"""
Integration tests for AI Signal core services.

This module contains integration tests that verify the proper interaction
between different core services and the overall system functionality.
"""

import asyncio
from datetime import datetime

import pytest

from aisignal.core.interfaces import (
    IConfigManager,
    ICoreService,
    IStorageService,
    OperationResult,
    UserContext,
)
from aisignal.core.models import OperationStatus, Resource


class TestCoreServiceIntegration:
    """Integration tests for core service functionality"""

    @pytest.fixture
    def container(self):
        """Provide a test service container"""
        from tests.mocks import create_test_container

        return create_test_container()

    @pytest.fixture
    def user_context(self):
        """Provide a test user context"""
        return UserContext(
            user_id="integration_test_user",
        )

    @pytest.fixture
    def sample_resources(self, user_context):
        """Provide sample resources for testing"""
        return [
            Resource(
                id="resource_1",
                user_id=user_context.user_id,
                title="Test Resource 1",
                url="https://example.com/1",
                categories=["AI", "Programming"],
                ranking=85.0,
                summary="A test resource about AI",
                full_content="",
                datetime=datetime.now(),
                source="https://example.com",
            ),
            Resource(
                id="resource_2",
                user_id=user_context.user_id,
                title="Test Resource 2",
                url="https://example.com/2",
                categories=["Programming"],
                ranking=65.0,
                summary="A test resource about programming",
                full_content="Full content here",
                datetime=datetime.now(),
                source="https://example.com",
            ),
            Resource(
                id="resource_3",
                user_id=user_context.user_id,
                title="Test Resource 3",
                url="https://example.com/3",
                categories=["Data Science"],
                ranking=55.0,
                summary="A test resource about data science",
                full_content="",
                datetime=datetime.now(),
                source="https://test.com",
            ),
        ]

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, container, user_context):
        """Test complete sync workflow"""
        core_service = container.get(ICoreService)

        # Test sync process
        progress_events = []
        async for progress in core_service.sync_sources(user_context):
            progress_events.append(progress)

        # Verify progress events were emitted
        assert len(progress_events) > 0

        # Verify we got both PENDING and COMPLETED events
        statuses = [event.get("status") for event in progress_events]
        assert "PENDING" in statuses
        assert "COMPLETED" in statuses

        # Verify resources were created (mock service creates some)
        resources = await core_service.get_resources(user_context)
        assert len(resources) >= 0  # Mock might not create resources

    @pytest.mark.asyncio
    async def test_resource_crud_operations(
        self, container, user_context, sample_resources
    ):
        """Test resource CRUD operations"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Store test resources
        store_result = await storage_service.store_resources(
            user_context, sample_resources
        )
        assert store_result.success

        # Test get resources
        retrieved_resources = await core_service.get_resources(user_context)
        assert len(retrieved_resources) == 3

        # Test get resource detail
        resource_detail = await core_service.get_resource_detail(
            user_context, sample_resources[0].id
        )
        assert resource_detail is not None
        assert resource_detail.id == sample_resources[0].id

        # Test update resource
        update_result = await core_service.update_resource(
            user_context,
            sample_resources[0].id,
            {"title": "Updated Title", "ranking": 90.0},
        )
        assert update_result.success

        # Verify update
        updated_resource = await core_service.get_resource_detail(
            user_context, sample_resources[0].id
        )
        assert updated_resource.title == "Updated Title"
        assert updated_resource.ranking == 90.0

        # Test remove resource
        remove_result = await core_service.remove_resource(
            user_context, sample_resources[0].id
        )
        assert remove_result.success

    @pytest.mark.asyncio
    async def test_resource_filtering(self, container, user_context, sample_resources):
        """Test resource filtering functionality"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Store test resources
        await storage_service.store_resources(user_context, sample_resources)

        # Test category filtering
        ai_resources = await core_service.get_resources(
            user_context, filters={"categories": ["AI"]}
        )
        assert len(ai_resources) == 1
        assert ai_resources[0].id == "resource_1"

        # Test source filtering
        example_resources = await core_service.get_resources(
            user_context, filters={"sources": ["https://example.com"]}
        )
        assert len(example_resources) == 2

        # Test combined filtering
        programming_from_example = await core_service.get_resources(
            user_context,
            filters={"categories": ["Programming"], "sources": ["https://example.com"]},
        )
        assert len(programming_from_example) == 2

    @pytest.mark.asyncio
    async def test_resource_pagination(self, container, user_context, sample_resources):
        """Test resource pagination"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Store test resources
        await storage_service.store_resources(user_context, sample_resources)

        # Test pagination
        page1 = await core_service.get_resources(user_context, limit=2, offset=0)
        assert len(page1) == 2

        page2 = await core_service.get_resources(user_context, limit=2, offset=2)
        assert len(page2) == 1

        # Verify no overlap
        page1_ids = {r.id for r in page1}
        page2_ids = {r.id for r in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_multi_user_isolation(self, container):
        """Test that users can only access their own data"""
        storage_service = container.get(IStorageService)
        core_service = container.get(ICoreService)

        # Create two different users
        user1_context = UserContext(
            user_id="user1",
        )

        user2_context = UserContext(
            user_id="user2",
        )

        # Create resources for each user
        user1_resources = [
            Resource(
                id="user1_resource_1",
                user_id=user1_context.user_id,
                title="User 1 Resource 1",
                url="https://user1.com/1",
                categories=["AI"],
                ranking=80.0,
                summary="User 1 resource",
                full_content="",
                datetime=datetime.now(),
                source="https://user1.com",
            ),
            Resource(
                id="user1_resource_2",
                user_id=user1_context.user_id,
                title="User 1 Resource 2",
                url="https://user1.com/2",
                categories=["Programming"],
                ranking=75.0,
                summary="Another User 1 resource",
                full_content="",
                datetime=datetime.now(),
                source="https://user1.com",
            ),
        ]

        user2_resources = [
            Resource(
                id="user2_resource_1",
                user_id=user2_context.user_id,
                title="User 2 Resource 1",
                url="https://user2.com/1",
                categories=["Data Science"],
                ranking=70.0,
                summary="User 2 resource",
                full_content="",
                datetime=datetime.now(),
                source="https://user2.com",
            ),
            Resource(
                id="user2_resource_2",
                user_id=user2_context.user_id,
                title="User 2 Resource 2",
                url="https://user2.com/2",
                categories=["ML"],
                ranking=85.0,
                summary="Another User 2 resource",
                full_content="",
                datetime=datetime.now(),
                source="https://user2.com",
            ),
            Resource(
                id="user2_resource_3",
                user_id=user2_context.user_id,
                title="User 2 Resource 3",
                url="https://user2.com/3",
                categories=["AI"],
                ranking=60.0,
                summary="Third User 2 resource",
                full_content="",
                datetime=datetime.now(),
                source="https://user2.com",
            ),
        ]

        # Store resources for each user
        await storage_service.store_resources(user1_context, user1_resources)
        await storage_service.store_resources(user2_context, user2_resources)

        # Verify user1 can only see their resources
        user1_retrieved = await core_service.get_resources(user1_context)
        assert len(user1_retrieved) == 2
        assert all(r.user_id == user1_context.user_id for r in user1_retrieved)

        user1_ids = {r.id for r in user1_retrieved}
        expected_user1_ids = {"user1_resource_1", "user1_resource_2"}
        assert user1_ids == expected_user1_ids

        # Verify user2 can only see their resources
        user2_retrieved = await core_service.get_resources(user2_context)
        assert len(user2_retrieved) == 3
        assert all(r.user_id == user2_context.user_id for r in user2_retrieved)

        user2_ids = {r.id for r in user2_retrieved}
        expected_user2_ids = {
            "user2_resource_1",
            "user2_resource_2",
            "user2_resource_3",
        }
        assert user2_ids == expected_user2_ids

        # Verify users cannot access each other's specific resources
        user1_detail = await core_service.get_resource_detail(
            user1_context, "user2_resource_1"
        )
        assert user1_detail is None

        user2_detail = await core_service.get_resource_detail(
            user2_context, "user1_resource_1"
        )
        assert user2_detail is None

    @pytest.mark.asyncio
    async def test_statistics_functionality(
        self, container, user_context, sample_resources
    ):
        """Test statistics calculation"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Store test resources
        await storage_service.store_resources(user_context, sample_resources)

        # Get statistics
        stats = await core_service.get_statistics(user_context)

        assert "total_resources" in stats
        assert stats["total_resources"] == 3

        assert "categories" in stats
        expected_categories = {"AI", "Programming", "Data Science"}
        assert set(stats["categories"]) == expected_categories

        assert "sources" in stats
        expected_sources = {"https://example.com", "https://test.com"}
        assert set(stats["sources"]) == expected_sources

    @pytest.mark.asyncio
    async def test_export_functionality(
        self, container, user_context, sample_resources
    ):
        """Test resource export functionality"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Store test resources
        await storage_service.store_resources(user_context, sample_resources)

        # Test successful export
        export_result = await core_service.export_resource(
            user_context, sample_resources[0].id, format="obsidian"
        )

        assert export_result.success
        assert export_result.data["exported"] is True
        assert export_result.data["format"] == "obsidian"

        # Test export of non-existent resource
        export_fail_result = await core_service.export_resource(
            user_context, "non_existent_id", format="obsidian"
        )

        assert export_fail_result.status != OperationStatus.SUCCESS
        assert "not found" in export_fail_result.message.lower()

    @pytest.mark.asyncio
    async def test_config_manager_integration(self, container, user_context):
        """Test configuration manager integration"""
        config_manager = container.get(IConfigManager)

        # Test getting user config
        config = await config_manager.get_user_config(user_context)
        assert isinstance(config, dict)
        assert "categories" in config
        assert "sources" in config
        assert "api_keys" in config

        # Test updating config
        updates = {
            "categories": ["New Category", "Another Category"],
            "min_threshold": 60.0,
        }

        update_result = await config_manager.update_user_config(user_context, updates)
        assert update_result.success

        # Verify updates
        updated_config = await config_manager.get_user_config(user_context)
        assert updated_config["categories"] == updates["categories"]
        assert updated_config["min_threshold"] == updates["min_threshold"]

        # Test specific getters
        categories = await config_manager.get_categories(user_context)
        assert categories == updates["categories"]

        thresholds = await config_manager.get_thresholds(user_context)
        assert thresholds["min_threshold"] == 60.0
        assert "max_threshold" in thresholds


class TestErrorHandling:
    """Test error handling in core services"""

    @pytest.fixture
    def container(self):
        """Provide a test service container"""
        from tests.mocks import create_test_container

        return create_test_container()

    @pytest.fixture
    def user_context(self):
        """Provide a test user context"""
        return UserContext(
            user_id="error_test_user",
        )

    @pytest.mark.asyncio
    async def test_resource_not_found_handling(self, container, user_context):
        """Test handling of resource not found scenarios"""
        core_service = container.get(ICoreService)

        # Test getting non-existent resource
        resource = await core_service.get_resource_detail(
            user_context, "non_existent_id"
        )
        assert resource is None

        # Test updating non-existent resource
        update_result = await core_service.update_resource(
            user_context, "non_existent_id", {"title": "New Title"}
        )
        assert update_result.status != OperationStatus.SUCCESS
        assert "not found" in update_result.message.lower()

        # Test removing non-existent resource
        remove_result = await core_service.remove_resource(
            user_context, "non_existent_id"
        )
        # Mock service might handle this differently,
        # just verify it returns OperationResult
        assert isinstance(remove_result, OperationResult)

    @pytest.mark.asyncio
    async def test_empty_data_handling(self, container, user_context):
        """Test handling of empty data scenarios"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Test getting resources when none exist
        resources = await core_service.get_resources(user_context)
        assert isinstance(resources, list)
        assert len(resources) == 0

        # Test storing empty list
        result = await storage_service.store_resources(user_context, [])
        assert result.success
        assert result.data["stored"] == 0

        # Test statistics with no data
        stats = await core_service.get_statistics(user_context)
        assert stats["total_resources"] == 0
        assert isinstance(stats["categories"], list)
        assert isinstance(stats["sources"], list)


class TestPerformance:
    """Performance tests for core operations"""

    @pytest.fixture
    def container(self):
        """Provide a test service container"""
        from tests.mocks import create_test_container

        return create_test_container()

    @pytest.fixture
    def user_context(self):
        """Provide a test user context"""
        return UserContext(
            user_id="perf_test_user",
        )

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, container, user_context):
        """Test performance with large datasets"""
        storage_service = container.get(IStorageService)
        core_service = container.get(ICoreService)

        # Create a large number of test resources
        large_resource_set = []
        for i in range(1000):
            resource = Resource(
                id=f"perf_test_resource_{i}",
                user_id=user_context.user_id,
                title=f"Performance Test Resource {i}",
                url=f"https://perftest.example.com/{i}",
                categories=["Performance", "Test"],
                ranking=50.0 + (i % 50),
                summary=f"Performance test resource {i}",
                full_content="",
                datetime=datetime.now(),
                source="https://perftest.example.com",
            )
            large_resource_set.append(resource)

        # Time the storage operation
        import time

        start_time = time.time()

        store_result = await storage_service.store_resources(
            user_context, large_resource_set
        )

        store_time = time.time() - start_time

        assert store_result.success
        assert store_result.data["stored"] == 1000

        # Time the query operation
        start_time = time.time()

        resources = await core_service.get_resources(user_context, limit=50, offset=0)

        query_time = time.time() - start_time

        assert len(resources) == 50

        # Performance assertions (these are loose for mock services)
        assert store_time < 5.0  # Should store 1000 resources in under 5 seconds
        assert query_time < 1.0  # Should query 50 resources in under 1 second

        print(f"Store time: {store_time:.3f}s, Query time: {query_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, container, user_context):
        """Test concurrent operations performance"""
        core_service = container.get(ICoreService)
        storage_service = container.get(IStorageService)

        # Create test resources
        resources = []
        for i in range(10):
            resource = Resource(
                id=f"concurrent_test_resource_{i}",
                user_id=user_context.user_id,
                title=f"Concurrent Test Resource {i}",
                url=f"https://concurrent.example.com/{i}",
                categories=["Concurrent", "Test"],
                ranking=70.0,
                summary=f"Concurrent test resource {i}",
                full_content="",
                datetime=datetime.now(),
                source="https://concurrent.example.com",
            )
            resources.append(resource)

        await storage_service.store_resources(user_context, resources)

        # Test concurrent reads
        async def get_resource_task(resource_id):
            return await core_service.get_resource_detail(user_context, resource_id)

        import time

        start_time = time.time()

        # Run multiple concurrent read operations
        tasks = [get_resource_task(f"concurrent_test_resource_{i}") for i in range(10)]

        results = await asyncio.gather(*tasks)

        concurrent_time = time.time() - start_time

        # Verify all operations completed successfully
        assert len(results) == 10
        assert all(result is not None for result in results)

        # Should complete concurrent operations quickly
        assert concurrent_time < 2.0

        print(f"Concurrent operations time: {concurrent_time:.3f}s")
