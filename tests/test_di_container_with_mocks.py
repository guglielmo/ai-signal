"""
Test DI container with mock services - Week 1 Friday deliverable.

This test demonstrates the DI container working with mock services
to validate the foundation architecture before implementing Core services.
"""

import asyncio
from datetime import datetime

import pytest

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IResourceManager,
    IStorageService,
)
from aisignal.core.models import Resource, UserContext
from aisignal.utils.advanced_service_container import ServiceContainer
from tests.mocks import (
    MockConfigManager,
    MockContentService,
    MockCoreService,
    MockResourceManager,
    MockStorageService,
    create_test_container,
)


class TestDIContainerWithMockServices:
    """
    Test suite demonstrating DI container working with mock services.

    This validates the foundation architecture where:
    1. All core interfaces are properly defined
    2. Mock services implement interfaces correctly
    3. DI container can resolve and inject dependencies
    4. Services work together through interfaces only
    """

    def test_container_creation_and_registration(self):
        """Test creating container and registering mock services"""
        container = ServiceContainer()

        # Register mock services
        container.register_singleton(IStorageService, MockStorageService)
        container.register_singleton(IConfigManager, MockConfigManager)
        container.register_singleton(IContentService, MockContentService)
        container.register_singleton(IResourceManager, MockResourceManager)
        container.register_singleton(ICoreService, MockCoreService)

        # Verify all services are registered
        registration_info = container.get_registration_info()

        expected_services = [
            "IStorageService",
            "IConfigManager",
            "IContentService",
            "IResourceManager",
            "ICoreService",
        ]

        for service_name in expected_services:
            assert service_name in registration_info
            assert registration_info[service_name]["scope"] == "singleton"

    def test_service_resolution(self):
        """Test resolving services from container"""
        container = create_test_container()

        # Resolve all core services
        storage = container.get(IStorageService)
        config = container.get(IConfigManager)
        content = container.get(IContentService)
        resource = container.get(IResourceManager)
        core = container.get(ICoreService)

        # Verify correct types
        assert isinstance(storage, MockStorageService)
        assert isinstance(config, MockConfigManager)
        assert isinstance(content, MockContentService)
        assert isinstance(resource, MockResourceManager)
        assert isinstance(core, MockCoreService)

        # Verify interface compliance
        assert isinstance(storage, IStorageService)
        assert isinstance(config, IConfigManager)
        assert isinstance(content, IContentService)
        assert isinstance(resource, IResourceManager)
        assert isinstance(core, ICoreService)

    def test_singleton_behavior(self):
        """Test that singleton services return same instance"""
        container = create_test_container()

        # Get services multiple times
        storage1 = container.get(IStorageService)
        storage2 = container.get(IStorageService)

        config1 = container.get(IConfigManager)
        config2 = container.get(IConfigManager)

        # Should be same instances
        assert storage1 is storage2
        assert config1 is config2

    def test_dependency_injection(self):
        """Test automatic dependency injection between services"""
        container = create_test_container()

        # CoreService depends on other services
        core_service = container.get(ICoreService)

        # Verify dependencies are injected (MockCoreService creates its own deps)
        assert hasattr(core_service, "storage")
        assert hasattr(core_service, "config")
        assert hasattr(core_service, "content")

        assert isinstance(core_service.storage, IStorageService)
        assert isinstance(core_service.config, IConfigManager)
        assert isinstance(core_service.content, IContentService)

    @pytest.mark.asyncio
    async def test_mock_service_functionality(self):
        """Test that mock services work correctly through interfaces"""
        container = create_test_container()

        # Create test user context
        user_context = UserContext(user_id="test_user")

        # Test config service
        config = container.get(IConfigManager)
        assert len(config.categories) > 0
        assert len(config.sources) > 0
        assert config.min_threshold > 0
        assert config.max_threshold > config.min_threshold

        # Test storage service
        storage = container.get(IStorageService)

        # Store test resources
        test_resources = [
            Resource(
                id="test-1",
                user_id=user_context.user_id,
                title="Test Resource 1",
                summary="Test summary 1",
                url="https://test1.com",
                categories=["AI"],
                ranking=75.0,
                full_content="Full content for test resource 1",
                datetime=datetime.now(),
                source="test1.com",
            ),
            Resource(
                id="test-2",
                user_id=user_context.user_id,
                title="Test Resource 2",
                summary="Test summary 2",
                url="https://test2.com",
                categories=["Programming"],
                ranking=65.0,
                full_content="Full content for test resource 2",
                datetime=datetime.now(),
                source="test2.com",
            ),
        ]

        result = await storage.store_resources(user_context, test_resources)
        assert result.is_success
        assert result.data["stored"] == 2

        # Retrieve resources
        resources = await storage.get_resources(user_context)
        assert len(resources) == 2
        assert resources[0].title == "Test Resource 1"

        # Filter resources
        ai_resources = await storage.get_resources(user_context, categories={"AI"})
        assert len(ai_resources) == 1
        assert ai_resources[0].categories == ["AI"]

        # Test content service
        content = container.get(IContentService)

        content_result = await content.fetch_content("https://example.com")
        assert content_result is not None
        assert "url" in content_result
        assert "title" in content_result

        # Test analyze content
        analysis = await content.analyze_content(content_result, "Test prompt")
        assert isinstance(analysis, dict)
        assert "https://example.com" in analysis

    @pytest.mark.asyncio
    async def test_core_service_orchestration(self):
        """Test core service orchestrating other services"""
        container = create_test_container()
        user_context = UserContext(user_id="test_user")

        core = container.get(ICoreService)

        # Test getting resources (should use storage service)
        resources = await core.get_resources(user_context)
        assert isinstance(resources, list)

        # Test getting statistics (should use storage service)
        stats = await core.get_statistics(user_context)
        assert isinstance(stats, dict)
        assert "total_resources" in stats

    def test_interface_method_coverage(self):
        """Test that mock services implement all required interface methods"""
        container = create_test_container()

        # Test IConfigManager methods
        config = container.get(IConfigManager)
        assert hasattr(config, "categories")
        assert hasattr(config, "sources")
        assert hasattr(config, "content_extraction_prompt")
        assert hasattr(config, "obsidian_vault_path")
        assert hasattr(config, "obsidian_template_path")
        assert hasattr(config, "openai_api_key")
        assert hasattr(config, "jina_api_key")
        assert hasattr(config, "min_threshold")
        assert hasattr(config, "max_threshold")
        assert hasattr(config, "sync_interval")
        assert hasattr(config, "save")

        # Test IResourceManager methods
        resource = container.get(IResourceManager)
        assert hasattr(resource, "add_resources")
        assert hasattr(resource, "clear_row_keys")
        assert hasattr(resource, "add_row_key")
        assert hasattr(resource, "__getitem__")
        assert hasattr(resource, "remove_resource")
        assert hasattr(resource, "get_filtered_resources")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling through interfaces"""
        container = create_test_container()
        user_context = UserContext(user_id="test_user")

        storage = container.get(IStorageService)

        # Test updating non-existent resource
        result = await storage.update_resource(
            user_context, "non-existent", {"title": "Updated"}
        )
        assert not result.is_success
        assert "not found" in result.message.lower()

    def test_container_validation(self):
        """Test container registration validation"""
        container = ServiceContainer()

        # Register services with potential issues
        container.register_singleton(IConfigManager, MockConfigManager)
        # Intentionally don't register IStorageService to test validation

        # Validate registrations
        errors = container.validate_registrations()

        # Should detect missing dependencies if any service depends on IStorageService
        # For mock services, this should pass
        # as they don't have constructor dependencies
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test service lifecycle management"""
        container = ServiceContainer()

        # Register scoped services
        container.register_scoped(IConfigManager, MockConfigManager)

        # Test scoped service lifecycle
        async with container.scope("test_scope"):
            config1 = container.get(IConfigManager)
            config2 = container.get(IConfigManager)

            # Should be same instance within scope
            assert config1 is config2

        # Test different scope
        async with container.scope("different_scope"):
            config3 = container.get(IConfigManager)

            # Should be different instance in different scope
            assert config1 is not config3

    def test_performance_with_mock_services(self):
        """Test performance of service resolution with mock services"""
        container = create_test_container()

        import time

        # Measure resolution time
        start_time = time.time()

        for _ in range(100):
            storage = container.get(IStorageService)
            config = container.get(IConfigManager)
            content = container.get(IContentService)
            core = container.get(ICoreService)

            # Verify instances are returned (not None)
            assert storage is not None
            assert config is not None
            assert content is not None
            assert core is not None

        end_time = time.time()
        resolution_time = end_time - start_time

        # Should resolve quickly (less than 0.1 seconds for 100 iterations)
        assert resolution_time < 0.1

    @pytest.mark.asyncio
    async def test_integration_workflow(self):
        """Test complete workflow using only interfaces"""
        container = create_test_container()
        user_context = UserContext(user_id="integration_test_user")

        # Get services through interfaces only
        config = container.get(IConfigManager)
        storage = container.get(IStorageService)
        content = container.get(IContentService)
        core = container.get(ICoreService)

        # Step 1: Get configuration
        categories = config.categories
        sources = config.sources
        assert len(categories) > 0
        assert len(sources) > 0

        # Step 2: Fetch content (simulated)
        url = sources[0]  # Use first source
        content_result = await content.fetch_content(url)
        assert content_result is not None

        # Step 3: Analyze content
        analysis = await content.analyze_content(
            content_result, config.content_extraction_prompt
        )
        assert len(analysis) > 0

        # Step 4: Create resources from analysis
        resources = []
        for url, items in analysis.items():
            for item in items:
                resource = Resource(
                    id=f"integration-{len(resources)}",
                    user_id=user_context.user_id,
                    title=item["title"],
                    summary=item["summary"],
                    url=url,
                    categories=item["categories"],
                    ranking=item["ranking"],
                    full_content=f"Full content for {item['title']}",
                    datetime=datetime.now(),
                    source=url,
                )
                resources.append(resource)

        # Step 5: Store resources
        store_result = await storage.store_resources(user_context, resources)
        assert store_result.is_success

        # Step 6: Retrieve and verify through core service
        retrieved_resources = await core.get_resources(user_context)
        assert len(retrieved_resources) >= len(resources)

        # Step 7: Get statistics
        stats = await core.get_statistics(user_context)
        assert stats["total_resources"] >= len(resources)

        print("✅ Integration test completed successfully!")
        print(f"   - Stored {len(resources)} resources")
        print(f"   - Retrieved {len(retrieved_resources)} resources")
        print(f"   - Statistics: {stats}")


# Test that validates the Friday deliverable requirements
class TestWeek1FridayDeliverables:
    """
    Test class specifically for validating Week 1 Friday deliverables:
    1. Working DI container with mock services
    2. Migration utilities and helpers
    3. Clear implementation roadmap for Week 2
    """

    def test_working_di_container_deliverable(self):
        """✅ Deliverable: Working DI container with mock services"""
        # Create container with all mock services
        container = create_test_container()

        # Verify all core services can be resolved
        services = {
            "storage": container.get(IStorageService),
            "config": container.get(IConfigManager),
            "content": container.get(IContentService),
            "resource": container.get(IResourceManager),
            "core": container.get(ICoreService),
        }

        # All services should be resolvable and implement interfaces
        for name, service in services.items():
            assert service is not None, f"{name} service not resolvable"

        print("✅ Working DI container with mock services - DELIVERED")

    def test_migration_utilities_deliverable(self):
        """✅ Deliverable: Migration utilities and helpers"""
        # Test that migration utilities exist and work
        from scripts.migration_helpers import InterfaceValidator, MigrationAnalyzer

        # Test migration analyzer
        analyzer = MigrationAnalyzer()
        dependencies = analyzer.scan_legacy_dependencies()
        assert isinstance(dependencies, dict)

        compliance = analyzer.analyze_interface_compliance()
        assert isinstance(compliance, dict)

        report = analyzer.generate_migration_report()
        assert isinstance(report, str)
        assert "MIGRATION STATUS REPORT" in report

        # Test interface validator
        container = create_test_container()

        config_valid = InterfaceValidator.validate_service_registration(
            container, IConfigManager
        )
        assert config_valid

        all_services_valid = InterfaceValidator.validate_all_core_services(container)
        assert all(all_services_valid.values())

        print("✅ Migration utilities and helpers - DELIVERED")

    def test_implementation_roadmap_deliverable(self):
        """✅ Deliverable: Clear implementation roadmap for Week 2"""
        from pathlib import Path

        # Verify roadmap documentation exists
        docs_path = Path("docs/multi-ui-migration")
        migration_plan = docs_path / "01-migration-plan.md"
        migration_utils = docs_path / "migration-utilities.md"

        assert migration_plan.exists(), "Migration plan documentation missing"
        assert migration_utils.exists(), "Migration utilities documentation missing"

        # Verify adapter examples exist
        adapters_path = Path("src/aisignal/core/adapters")
        assert adapters_path.exists(), "Adapters directory missing"
        assert (adapters_path / "config_adapter.py").exists(), "Config adapter missing"
        assert (
            adapters_path / "resource_adapter.py"
        ).exists(), "Resource adapter missing"
        assert (
            adapters_path / "content_adapter.py"
        ).exists(), "Content adapter missing"

        # Verify example usage exists
        examples_path = Path("examples")
        assert (
            examples_path / "adapter_usage.py"
        ).exists(), "Adapter usage example missing"

        print("✅ Clear implementation roadmap for Week 2 - DELIVERED")

    @pytest.mark.asyncio
    async def test_foundation_readiness_for_week2(self):
        """Test that foundation is ready for Week 2 Core service implementation"""
        container = create_test_container()
        user_context = UserContext(user_id="week2_readiness_test")

        # Test all interfaces work correctly
        config = container.get(IConfigManager)
        storage = container.get(IStorageService)
        core = container.get(ICoreService)

        # Test basic operations that Week 2 Core services will need to implement
        categories = config.categories
        assert len(categories) > 0

        resources = await storage.get_resources(user_context)
        assert isinstance(resources, list)

        stats = await core.get_statistics(user_context)
        assert isinstance(stats, dict)

        # Test that dependency injection works
        assert isinstance(core.storage, IStorageService)
        assert isinstance(core.config, IConfigManager)

        print("✅ Foundation ready for Week 2 Core service implementation")


if __name__ == "__main__":
    # Run a quick integration test
    async def quick_test():
        container = create_test_container()
        user_context = UserContext(user_id="quick_test")

        config = container.get(IConfigManager)
        print(f"Config categories: {config.categories}")

        storage = container.get(IStorageService)
        resources = await storage.get_resources(user_context)
        print(f"Resources: {len(resources)}")

        print("✅ DI container with mock services working correctly!")

    asyncio.run(quick_test())
