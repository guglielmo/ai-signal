"""
Core Service Implementation

This module implements the ICoreService interface, which orchestrates
all core business logic by coordinating Storage, Config, and Content services.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IEventBus,
    IStorageService,
)
from aisignal.core.models import (
    OperationResult,
    Resource,
    ResourceUpdatedEvent,
    SyncCompletedEvent,
    SyncProgressEvent,
    UserContext,
)


class CoreService(ICoreService):
    """
    Main orchestrator service that coordinates Storage, Config, and Content services.

    This service implements the core business logic of AI Signal by delegating
    operations to the appropriate specialized services and handling cross-service
    coordination when needed.
    """

    def __init__(
        self,
        storage_service: IStorageService,
        config_manager: IConfigManager,
        content_service: IContentService,
        event_bus: Optional[IEventBus] = None,
    ):
        """
        Initialize the CoreService with its dependencies.

        Args:
            storage_service: Service for data persistence operations
            config_manager: Service for configuration management
            content_service: Service for content fetching and analysis
            event_bus: Optional event bus for publishing events
        """
        self.storage = storage_service
        self.config = config_manager
        self.content = content_service
        self.event_bus = event_bus

    async def get_resources(
        self,
        user_context: UserContext,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "ranking",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        """
        Retrieve resources with filters and sorting.

        Args:
            user_context: Context of the user making the request
            filters: Optional filters to apply (categories, sources, etc.)
            sort_by: Field to sort by ("ranking", "datetime", etc.)
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            List of filtered and sorted resources
        """
        # Extract filter parameters
        categories = None
        sources = None
        sort_desc = True

        if filters:
            categories = filters.get("categories")
            sources = filters.get("sources")
            sort_desc = filters.get("sort_desc", True)

            # Convert lists to sets if needed
            if categories and isinstance(categories, list):
                categories = set(categories)
            if sources and isinstance(sources, list):
                sources = set(sources)

        # Delegate to storage service
        return await self.storage.get_resources(
            user_context=user_context,
            categories=categories,
            sources=sources,
            sort_by=sort_by,
            sort_desc=sort_desc,
            limit=limit,
            offset=offset,
        )

    async def get_resource_detail(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """
        Retrieve complete details of a specific resource.

        Args:
            user_context: Context of the user making the request
            resource_id: ID of the resource to retrieve

        Returns:
            Resource object with all details, or None if not found
        """
        return await self.storage.get_resource_by_id(user_context, resource_id)

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """
        Update a resource with new values.

        Args:
            user_context: Context of the user making the request
            resource_id: ID of the resource to update
            updates: Dictionary of fields to update

        Returns:
            OperationResult indicating success or failure
        """
        # Input validation
        if not updates:
            return OperationResult.invalid_input("No updates provided")

        # Validate that the resource exists
        existing = await self.storage.get_resource_by_id(user_context, resource_id)
        if not existing:
            return OperationResult.not_found(f"Resource {resource_id} not found")

        # Delegate to storage service
        result = await self.storage.update_resource(user_context, resource_id, updates)

        # Emit event if successful and event bus is available
        if result.is_success and self.event_bus:
            self.event_bus.publish(
                ResourceUpdatedEvent(
                    user_context=user_context,
                    resource_id=resource_id,
                    operation="updated",
                    resource=result.data,
                )
            )

        return result

    async def remove_resource(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        """
        Remove a resource (soft delete).

        Args:
            user_context: Context of the user making the request
            resource_id: ID of the resource to remove

        Returns:
            OperationResult indicating success or failure
        """
        # Validate that the resource exists
        existing = await self.storage.get_resource_by_id(user_context, resource_id)
        if not existing:
            return OperationResult.not_found(f"Resource {resource_id} not found")

        # Delegate to storage service
        result = await self.storage.mark_resource_removed(user_context, resource_id)

        # Emit event if successful and event bus is available
        if result.is_success and self.event_bus:
            self.event_bus.publish(
                ResourceUpdatedEvent(
                    user_context=user_context,
                    resource_id=resource_id,
                    operation="removed",
                    resource=result.data,
                )
            )

        return result

    async def get_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """
        Retrieve statistics for the user.

        Args:
            user_context: Context of the user making the request

        Returns:
            Dictionary with user statistics
        """
        return await self.storage.get_user_statistics(user_context)

    # =============================================================================
    # ADDITIONAL ORCHESTRATION METHODS
    # =============================================================================

    async def sync_sources(
        self, user_context: UserContext, source_urls: Optional[List[str]] = None
    ) -> OperationResult:
        """
        Synchronize content from configured sources.

        This method orchestrates the entire content synchronization workflow:
        1. Fetch content from sources
        2. Analyze content with AI
        3. Store new resources

        Args:
            user_context: Context of the user making the request
            source_urls: Optional list of specific sources to sync.
                        If None, syncs all configured sources.

        Returns:
            OperationResult with sync statistics
        """
        errors = []
        try:
            # Get sources from config if not specified
            if source_urls is None:
                source_urls = self.config.sources

            if not source_urls:
                return OperationResult.invalid_input("No sources configured")

            total_new_items = 0
            total_analyzed = 0
            total_sources = len(source_urls)

            # Emit initial progress event
            if self.event_bus:
                self.event_bus.publish(
                    SyncProgressEvent(
                        user_context=user_context,
                        current=0,
                        total=total_sources,
                        message="Starting sync...",
                    )
                )

            # Fetch content from each source
            content_results = []
            for idx, url in enumerate(source_urls, 1):
                # Emit progress event
                if self.event_bus:
                    self.event_bus.publish(
                        SyncProgressEvent(
                            user_context=user_context,
                            current=idx,
                            total=total_sources,
                            message=f"Fetching content from {url}...",
                        )
                    )

                try:
                    # Determine if URL is RSS feed or regular webpage
                    if any(
                        url.endswith(ext)
                        for ext in [".rss", ".atom", ".xml", "/feed", "/rss"]
                    ):
                        content = await self.content.fetch_rss_content(url)
                    else:
                        content = await self.content.fetch_content(url)

                    if content:
                        content_results.append(content)
                except Exception as e:
                    error_msg = f"Failed to fetch {url}: {str(e)}"
                    errors.append(error_msg)

            # Analyze content with AI
            if content_results:
                # Emit progress for analysis phase
                if self.event_bus:
                    self.event_bus.publish(
                        SyncProgressEvent(
                            user_context=user_context,
                            current=total_sources,
                            total=total_sources,
                            message="Analyzing content with AI...",
                        )
                    )

                analyzed_items = await self.content.analyze_content(
                    content_results, self.config.content_extraction_prompt
                )

                # Convert analyzed items to resources and store them
                for source_url, items in analyzed_items.items():
                    if items:
                        # Convert items to resources
                        resources = []
                        for item in items:
                            # Generate ID from URL hash since items don't have IDs
                            item_url = item.get("link", "")
                            item_id = hashlib.md5(item_url.encode()).hexdigest()

                            resource = Resource(
                                id=item_id,
                                user_id=user_context.user_id,
                                title=item.get("title", ""),
                                url=item_url,
                                categories=item.get("categories", []),
                                ranking=float(item.get("ranking", 0)),
                                summary=item.get("summary", ""),
                                full_content=item.get("full_content", ""),
                                datetime=datetime.now(),
                                source=source_url,
                            )
                            resources.append(resource)

                        # Store resources
                        result = await self.storage.store_resources(
                            user_context, resources
                        )
                        if result.is_success:
                            total_new_items += len(resources)

                            # Emit resource created events for each new resource
                            if self.event_bus:
                                for resource in resources:
                                    self.event_bus.publish(
                                        ResourceUpdatedEvent(
                                            user_context=user_context,
                                            resource_id=resource.id,
                                            operation="created",
                                            resource=resource,
                                        )
                                    )

                    total_analyzed += len(items)

            # Emit sync completed event
            if self.event_bus:
                self.event_bus.publish(
                    SyncCompletedEvent(
                        user_context=user_context,
                        success=True,
                        total_resources=total_analyzed,
                        new_resources=total_new_items,
                        updated_resources=0,
                        errors=errors,
                        message=f"Synced {len(source_urls)} sources, "
                        f"found {total_new_items} new items",
                    )
                )

            return OperationResult.success(
                data={
                    "sources_synced": len(source_urls),
                    "items_analyzed": total_analyzed,
                    "new_items": total_new_items,
                },
                message=f"Synced {len(source_urls)} sources, "
                f"found {total_new_items} new items",
            )

        except Exception as e:
            # Emit sync completed event with error
            if self.event_bus:
                self.event_bus.publish(
                    SyncCompletedEvent(
                        user_context=user_context,
                        success=False,
                        total_resources=0,
                        new_resources=0,
                        updated_resources=0,
                        errors=[str(e)],
                        message=f"Sync failed: {str(e)}",
                    )
                )
            return OperationResult.error(f"Sync failed: {str(e)}")

    async def search_resources(
        self,
        user_context: UserContext,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Resource]:
        """
        Search resources by text query.

        This is a placeholder for future full-text search implementation.
        Currently returns filtered resources that match the query in title or summary.

        TODO: Performance optimization needed for large datasets
            - Current implementation loads all resources into memory (O(n) scan)
            - Consider pushing search logic to storage layer for better performance
            - Evaluate SQLite FTS5 (Full-Text Search) or external search engine
            - Add pagination support for search results

        Args:
            user_context: Context of the user making the request
            query: Search query string
            filters: Optional additional filters

        Returns:
            List of matching resources
        """
        # Get all resources with filters
        resources = await self.get_resources(user_context, filters=filters)

        # Simple text matching (to be enhanced with proper search later)
        query_lower = query.lower()
        matching = [
            r
            for r in resources
            if query_lower in r.title.lower() or query_lower in r.summary.lower()
        ]

        return matching

    def get_config_value(self, key: str) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key to retrieve

        Returns:
            Configuration value

        Raises:
            ValueError: If the configuration key doesn't exist
        """
        if hasattr(self.config, key):
            return getattr(self.config, key)
        raise ValueError(f"Configuration key '{key}' not found")

    async def update_config(self, new_config: dict) -> OperationResult:
        """
        Update application configuration.

        Args:
            new_config: Dictionary with new configuration values

        Returns:
            OperationResult indicating success or failure
        """
        try:
            self.config.save(new_config)
            return OperationResult.success(message="Configuration updated successfully")
        except Exception as e:
            return OperationResult.error(f"Failed to update configuration: {str(e)}")
