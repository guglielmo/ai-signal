"""
Example demonstrating adapter pattern usage in AI Signal Core.

This example shows how to use adapters to wrap existing implementations
and work with the new Core architecture through dependency injection.
"""

import asyncio
from pathlib import Path

from aisignal.core.adapters.config_adapter import create_config_adapter
from aisignal.core.adapters.content_adapter import create_content_adapter
from aisignal.core.adapters.resource_adapter import create_resource_adapter
from aisignal.core.config import ConfigManager
from aisignal.core.interfaces import IConfigManager, IContentService, IResourceManager
from aisignal.core.resource_manager import ResourceManager
from aisignal.core.token_tracker import TokenTracker
from aisignal.services.storage import MarkdownSourceStorage, ParsedItemStorage
from aisignal.utils.advanced_service_container import ServiceContainer


async def adapter_pattern_example():
    """
    Demonstrates how to use adapters to integrate existing components
    with the new Core architecture through dependency injection.
    """
    print("=== AI Signal Adapter Pattern Example ===")

    # Step 1: Create existing implementations (legacy code)
    print("\n1. Creating existing implementations...")

    # Create existing ConfigManager
    config_manager = ConfigManager()
    print(f"   Created ConfigManager with {len(config_manager.categories)} categories")

    # Create existing ResourceManager
    resource_manager = ResourceManager()
    print(
        f"   Created ResourceManager "
        f"(empty: {len(resource_manager.resources)} resources)"
    )

    # Create storage components for ContentService
    storage_path = Path.home() / ".config" / "aisignal" / "storage"
    markdown_storage = MarkdownSourceStorage(storage_path / "sources.db")
    item_storage = ParsedItemStorage(storage_path / "items.db")
    token_tracker = TokenTracker()

    print(f"   Created storage components at {storage_path}")

    # Step 2: Create adapters that wrap existing implementations
    print("\n2. Creating adapters...")

    # Create config adapter
    config_adapter = create_config_adapter(config_manager)
    print("   Created ConfigManagerAdapter")

    # Create resource adapter
    resource_adapter = create_resource_adapter(resource_manager)
    print("   Created ResourceManagerAdapter")

    # Create content adapter
    content_adapter = create_content_adapter(
        jina_api_key=config_manager.jina_api_key,
        openai_api_key=config_manager.openai_api_key,
        categories=config_manager.categories,
        markdown_storage=markdown_storage,
        item_storage=item_storage,
        token_tracker=token_tracker,
        min_threshold=config_manager.min_threshold,
        max_threshold=config_manager.max_threshold,
    )
    print("   Created ContentServiceAdapter")

    # Step 3: Register adapters with dependency injection container
    print("\n3. Registering adapters with DI container...")

    container = ServiceContainer()

    # Register adapter instances (they implement the interfaces)
    container.register_instance(IConfigManager, config_adapter)
    container.register_instance(IResourceManager, resource_adapter)
    container.register_instance(IContentService, content_adapter)

    print("   Registered all adapters with ServiceContainer")

    # Step 4: Use services through interfaces (Core architecture)
    print("\n4. Using services through Core interfaces...")

    # Resolve services through DI container
    config_service = container.get(IConfigManager)
    resource_service = container.get(IResourceManager)

    # Use services through interfaces
    print(f"   Config categories: {config_service.categories}")
    print(f"   Config sources: {len(config_service.sources)} sources")
    print(f"   Resource count: {len(resource_service.get_filtered_resources())}")

    # Test content service (async)
    try:
        # This would normally fetch real content, but we're just showing the pattern
        print("   Content service is ready for fetching content")
        print(f"   Min threshold: {config_service.min_threshold}")
        print(f"   Max threshold: {config_service.max_threshold}")
    except Exception as e:
        print(f"   Content service error (expected in example): {type(e).__name__}")

    # Step 5: Demonstrate that changes to original objects are reflected
    print("\n5. Demonstrating adapter transparency...")

    # Add to original ResourceManager
    from datetime import datetime

    from aisignal.core.models import Resource

    test_resource = Resource(
        id="test-1",
        title="Test Resource",
        summary="A test resource for demonstration",
        url="https://example.com/test",
        categories=["AI"],
        ranking=75.0,
        datetime=datetime.now(),
        source="example.com",
    )

    # Add through original manager
    resource_manager.add_resources([test_resource])

    # Access through adapter - should see the new resource
    filtered_resources = resource_service.get_filtered_resources()
    print("   Added resource through original manager")
    print(f"   Resources accessible through adapter: {len(filtered_resources)}")

    if filtered_resources:
        print(f"   First resource title: {filtered_resources[0].title}")

    print("\n=== Adapter Pattern Example Complete ===")
    print("\nKey benefits demonstrated:")
    print("- Existing code unchanged (ConfigManager, ResourceManager, ContentService)")
    print("- New Core interfaces implemented through adapters")
    print("- Dependency injection works with wrapped services")
    print("- Transparent operation - changes visible through adapters")
    print("- Ready for gradual migration to pure Core implementations")


def migration_strategy_example():
    """
    Shows the migration strategy using adapters as a bridge.
    """
    print("\n=== Migration Strategy Example ===")

    print("\nMigration Path:")
    print("1. Week 1 (Current): Create interfaces and adapters")
    print("   - Existing code unchanged")
    print("   - Adapters provide interface compliance")
    print("   - DI container uses adapters")

    print("\n2. Week 2: Implement Core services")
    print("   - Create new Core service implementations")
    print("   - Register Core services instead of adapters")
    print("   - Adapters become fallback/comparison tools")

    print("\n3. Week 3: Refactor UI to use Core")
    print("   - UI depends only on interfaces")
    print("   - Can switch between adapters and Core services")
    print("   - Gradual testing and validation")

    print("\n4. Week 4-5: Complete migration")
    print("   - Remove adapters when Core services proven")
    print("   - Legacy implementations become optional")
    print("   - Clean Core architecture achieved")

    print("\nAdapter Benefits:")
    print("- Zero risk migration (existing code unchanged)")
    print("- Interface compliance from day 1")
    print("- Easy A/B testing of old vs new implementations")
    print("- Gradual migration without breaking changes")


if __name__ == "__main__":
    asyncio.run(adapter_pattern_example())
    migration_strategy_example()
