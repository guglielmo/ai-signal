"""
Mock services for AI Signal testing.

This module provides mock implementations of all core services
for use in unit and integration tests.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, Union

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IResourceManager,
    IStorageService,
)
from aisignal.core.models import OperationResult, Resource, UserContext


class MockResourceManager(IResourceManager):
    """Mock resource manager for testing"""

    def __init__(self):
        self.resources: List[Resource] = []
        self.row_key_map: Dict[str, int] = {}

    def add_resources(self, resources: List[Resource]) -> None:
        """Add resources to the collection"""
        self.resources.extend(resources)

    def clear_row_keys(self) -> None:
        """Clear all row key mappings"""
        self.row_key_map.clear()

    def add_row_key(self, row_key: str, resource_index: int) -> None:
        """Add a row key mapping"""
        self.row_key_map[row_key] = resource_index

    def __getitem__(self, row_key: str) -> Resource:
        """Get resource by row key"""
        if row_key not in self.row_key_map:
            raise KeyError(f"Row key {row_key} not found")
        index = self.row_key_map[row_key]
        return self.resources[index]

    def remove_resource(self, resource_id: str) -> None:
        """Mark resource as removed"""
        for resource in self.resources:
            if resource.id == resource_id:
                resource.removed = True
                break

    def get_filtered_resources(
        self,
        categories: Set[str] = None,
        sources: Set[str] = None,
        sort_by_datetime: bool = False,
    ) -> List[Resource]:
        """Filter and sort resources"""
        filtered = [r for r in self.resources if not r.removed]

        # Apply filters
        if categories:
            filtered = [
                r for r in filtered if any(cat in categories for cat in r.categories)
            ]
        if sources:
            filtered = [r for r in filtered if r.source in sources]

        # Sort
        if sort_by_datetime:
            filtered.sort(key=lambda r: r.datetime, reverse=True)
        else:
            filtered.sort(key=lambda r: (r.ranking, r.datetime), reverse=True)

        return filtered


class MockStorageService(IStorageService):
    """Mock storage service for testing"""

    def __init__(self):
        self.resources: Dict[str, List[Resource]] = {}
        self.content_cache: Dict[str, str] = {}

    async def get_resources(
        self,
        user_context: UserContext,
        categories: Optional[Set[str]] = None,
        sources: Optional[Set[str]] = None,
        sort_by: str = "ranking",
        sort_desc: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        user_resources = self.resources.get(user_context.user_id, [])

        # Apply filters
        filtered = [r for r in user_resources if not r.removed]
        if categories:
            filtered = [
                r for r in filtered if any(c in categories for c in r.categories)
            ]
        if sources:
            filtered = [r for r in filtered if r.source in sources]

        # Sort
        if sort_by == "ranking":
            filtered.sort(key=lambda r: r.ranking, reverse=sort_desc)
        elif sort_by == "datetime":
            filtered.sort(key=lambda r: r.datetime, reverse=sort_desc)

        # Apply pagination
        start = offset
        end = start + limit if limit else None
        return filtered[start:end]

    async def get_resource_by_id(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        user_resources = self.resources.get(user_context.user_id, [])
        return next((r for r in user_resources if r.id == resource_id), None)

    async def store_resources(
        self, user_context: UserContext, resources: List[Resource]
    ) -> OperationResult:
        if user_context.user_id not in self.resources:
            self.resources[user_context.user_id] = []

        self.resources[user_context.user_id].extend(resources)
        return OperationResult.success(data={"stored": len(resources)})

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        user_resources = self.resources.get(user_context.user_id, [])

        for resource in user_resources:
            if resource.id == resource_id:
                for key, value in updates.items():
                    setattr(resource, key, value)
                return OperationResult.success(data=resource)

        return OperationResult.not_found("Resource not found")

    async def mark_resource_removed(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        return await self.update_resource(user_context, resource_id, {"removed": True})

    async def get_sources_content(
        self, user_context: UserContext, url: str
    ) -> Optional[str]:
        cache_key = f"{user_context.user_id}:{url}"
        return self.content_cache.get(cache_key)

    async def store_source_content(
        self, user_context: UserContext, url: str, content: str
    ) -> OperationResult:
        cache_key = f"{user_context.user_id}:{url}"
        self.content_cache[cache_key] = content
        return OperationResult.success()

    async def get_user_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        user_resources = self.resources.get(user_context.user_id, [])
        active_resources = [r for r in user_resources if not r.removed]
        return {
            "total_resources": len(active_resources),
            "categories": list(
                set(cat for r in active_resources for cat in r.categories)
            ),
            "sources": list(set(r.source for r in active_resources if r.source)),
        }


class MockConfigManager(IConfigManager):
    """Mock configuration manager for testing"""

    def __init__(self):
        self.configs: Dict[str, Dict[str, Any]] = {}

    @property
    def categories(self) -> List[str]:
        """Gets the list of categories from the configuration."""
        return ["AI", "Programming", "Data Science"]

    @property
    def sources(self) -> List[str]:
        """Retrieves the list of source strings from the configuration."""
        return ["https://example.com"]

    @property
    def content_extraction_prompt(self) -> str:
        """Retrieves the content extraction prompt from the configuration."""
        return "Extract key information from the following content:"

    @property
    def obsidian_vault_path(self) -> str:
        """Retrieves the path to the Obsidian vault as specified
        in the configuration."""
        return "/mock/obsidian/vault"

    @property
    def obsidian_template_path(self) -> str:
        """Retrieves the file path for the Obsidian template."""
        return "/mock/obsidian/template.md"

    @property
    def openai_api_key(self) -> str:
        """Retrieves the OpenAI API key from the configuration."""
        return "mock-openai-api-key"

    @property
    def jina_api_key(self) -> str:
        """Retrieves the Jina API key from the configuration."""
        return "mock-jina-api-key"

    @property
    def min_threshold(self) -> float:
        """Returns the minimum threshold value set in the current configuration."""
        return 50.0

    @property
    def max_threshold(self) -> float:
        """Gets the maximum threshold value from the current configuration."""
        return 80.0

    @property
    def sync_interval(self) -> int:
        """Gets the sync interval value from the current configuration."""
        return 24

    def save(self, new_config: dict) -> None:
        """
        Saves a new configuration by merging it with the existing configuration.

        Args:
            new_config: The new configuration values to be merged
            with the existing configuration.
        """
        # In the mock implementation, we don't actually save anything
        pass


class MockContentService(IContentService):
    """Mock content service for testing"""

    def __init__(self):
        self.mock_responses = {
            "https://example.com": "# Example Content\n\nSample markdown content",
            "https://test.com": "# Test Content\n\nTest markdown content",
        }

    async def fetch_content(self, url: str) -> Optional[Dict]:
        content = self.mock_responses.get(url, f"Mock content for {url}")
        return {
            "url": url,
            "title": f"Title for {url}",
            "content": content,
            "diff": None,
        }

    async def fetch_full_content(self, url: str) -> Optional[str]:
        return self.mock_responses.get(url, f"Full mock content for {url}")

    async def analyze_content(
        self,
        content_results: Union[Dict, List[Dict]],
        prompt_template: str,
        batch_size: int = 3500,
    ) -> Dict[str, List[Dict]]:
        results = {}

        # Handle single content result or list
        content_list = (
            [content_results] if isinstance(content_results, dict) else content_results
        )

        for content_item in content_list:
            url = content_item.get("url", "unknown")
            results[url] = [
                {
                    "title": f"Item 1 from {url}",
                    "summary": "Mock summary 1",
                    "categories": ["AI"],
                    "ranking": 75.0,
                },
                {
                    "title": f"Item 2 from {url}",
                    "summary": "Mock summary 2",
                    "categories": ["Programming"],
                    "ranking": 65.0,
                },
            ]

        return results


class MockCoreService(ICoreService):
    """Mock core service for testing"""

    def __init__(
        self,
        storage_service: IStorageService = None,
        config_manager: IConfigManager = None,
        content_service: IContentService = None,
    ):
        self.storage = storage_service or MockStorageService()
        self.config = config_manager or MockConfigManager()
        self.content = content_service or MockContentService()

    async def get_resources(
        self,
        user_context: UserContext,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "ranking",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        categories = None
        sources = None
        if filters:
            categories = filters.get("categories")
            sources = filters.get("sources")
            if categories:
                categories = set(categories)
            if sources:
                sources = set(sources)

        return await self.storage.get_resources(
            user_context,
            categories=categories,
            sources=sources,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

    async def get_resource_detail(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        return await self.storage.get_resource_by_id(user_context, resource_id)

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        return await self.storage.update_resource(user_context, resource_id, updates)

    async def remove_resource(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        return await self.storage.mark_resource_removed(user_context, resource_id)

    async def get_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        return await self.storage.get_user_statistics(user_context)

    async def sync_sources(self, user_context: UserContext, sources=None):
        """Mock sync with progress updates"""
        test_sources = sources or ["https://example.com"]

        for i, url in enumerate(test_sources):
            # Mock progress update
            progress = {"url": url, "status": "PENDING", "progress_percent": 0.0}
            yield progress

            await asyncio.sleep(0.01)  # Simulate work (shorter for tests)

            progress = {
                "url": url,
                "status": "COMPLETED",
                "progress_percent": 100.0,
                "items_found": 3,
                "new_items": 2,
            }
            yield progress

    async def export_resource(
        self, user_context: UserContext, resource_id: str, format="obsidian"
    ) -> OperationResult:
        resource = await self.get_resource_detail(user_context, resource_id)
        if resource:
            return OperationResult.success(data={"exported": True, "format": format})
        return OperationResult.not_found("Resource not found")


def create_test_container():
    """Create service container with mock services for testing"""
    from aisignal.utils.advanced_service_container import ServiceContainer

    container = ServiceContainer()

    # Register mock services
    container.register_singleton(IStorageService, MockStorageService)
    container.register_singleton(IConfigManager, MockConfigManager)
    container.register_singleton(IContentService, MockContentService)
    container.register_singleton(ICoreService, MockCoreService)
    container.register_singleton(IResourceManager, MockResourceManager)

    return container
