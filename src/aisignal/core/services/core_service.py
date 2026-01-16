"""
Core Service - Main orchestrator for AI Signal business logic.

This service coordinates all other services and provides a unified API
for the UI layer to interact with.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from aisignal.core.events import (
    EventBus,
    EventType,
    ResourceRemovedEvent,
    ResourcesLoadedEvent,
    ResourceUpdatedEvent,
    SyncCompletedEvent,
    SyncProgressEvent,
    get_event_bus,
)
from aisignal.core.interfaces import (
    IConfigManager,
    IContentService,
    ICoreService,
    IStorageService,
)
from aisignal.core.models import OperationResult, Resource, UserContext

logger = logging.getLogger(__name__)


class CoreService(ICoreService):
    """
    Main orchestrator service that coordinates all AI Signal operations.

    This service acts as a facade for the UI layer, providing a clean API
    that hides the complexity of coordinating multiple services.

    Emits events for UI updates via the event bus.

    Attributes:
        storage: Storage service for data persistence
        config: Configuration service
        content: Content fetching and analysis service
        event_bus: Event bus for publishing events
    """

    def __init__(
        self,
        storage_service: IStorageService,
        config_service: IConfigManager,
        content_service: Optional[IContentService] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """
        Initialize the CoreService with its dependencies.

        Args:
            storage_service: Service for data persistence
            config_service: Service for configuration management
            content_service: Optional service for content fetching/analysis
            event_bus: Optional event bus for publishing events (uses global if None)
        """
        self._storage = storage_service
        self._config = config_service
        self._content = content_service
        self._event_bus = event_bus or get_event_bus()
        logger.info("CoreService initialized")

    @property
    def storage(self) -> IStorageService:
        """Get the storage service."""
        return self._storage

    @property
    def config(self) -> IConfigManager:
        """Get the config service."""
        return self._config

    @property
    def content(self) -> Optional[IContentService]:
        """Get the content service (may be None if not configured)."""
        return self._content

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus for subscribing to events."""
        return self._event_bus

    # =========================================================================
    # ICoreService Implementation
    # =========================================================================

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
            user_context: User context for the operation
            filters: Optional filters dict with 'categories' and/or 'sources' keys
            sort_by: Field to sort by ("ranking" or "datetime")
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of filtered and sorted resources
        """
        # Parse filters
        categories: Optional[Set[str]] = None
        sources: Optional[Set[str]] = None

        if filters:
            if "categories" in filters and filters["categories"]:
                categories = set(filters["categories"])
            if "sources" in filters and filters["sources"]:
                sources = set(filters["sources"])

        # Determine sort direction
        sort_desc = True  # Default descending for both ranking and datetime

        try:
            resources = await self._storage.get_resources(
                user_context=user_context,
                categories=categories,
                sources=sources,
                sort_by=sort_by,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
            )
            logger.debug(
                f"Retrieved {len(resources)} resources for user {user_context.user_id}"
            )

            # Emit event for UI updates
            self._event_bus.emit(ResourcesLoadedEvent(count=len(resources)))

            return resources
        except Exception as e:
            logger.error(f"Error retrieving resources: {e}")
            return []

    async def get_resource_detail(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """
        Retrieve full details of a specific resource.

        Args:
            user_context: User context for the operation
            resource_id: ID of the resource to retrieve

        Returns:
            Resource with full details, or None if not found
        """
        try:
            resource = await self._storage.get_resource_by_id(user_context, resource_id)
            if resource:
                logger.debug(f"Retrieved resource detail: {resource_id}")
            else:
                logger.debug(f"Resource not found: {resource_id}")
            return resource
        except Exception as e:
            logger.error(f"Error retrieving resource detail {resource_id}: {e}")
            return None

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """
        Update a resource with the given changes.

        Args:
            user_context: User context for the operation
            resource_id: ID of the resource to update
            updates: Dictionary of fields to update

        Returns:
            OperationResult indicating success or failure
        """
        try:
            result = await self._storage.update_resource(
                user_context, resource_id, updates
            )
            if result.is_success:
                logger.info(f"Updated resource {resource_id}")
                # Emit event for UI updates
                self._event_bus.emit(
                    ResourceUpdatedEvent(
                        resource_id=resource_id,
                        updated_fields=list(updates.keys()),
                    )
                )
            else:
                logger.warning(f"Failed to update resource {resource_id}: {result.message}")
            return result
        except Exception as e:
            logger.error(f"Error updating resource {resource_id}: {e}")
            return OperationResult.error(f"Failed to update resource: {str(e)}")

    async def remove_resource(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        """
        Mark a resource as removed (soft delete).

        Args:
            user_context: User context for the operation
            resource_id: ID of the resource to remove

        Returns:
            OperationResult indicating success or failure
        """
        try:
            result = await self._storage.mark_resource_removed(user_context, resource_id)
            if result.is_success:
                logger.info(f"Removed resource {resource_id}")
                # Emit event for UI updates
                self._event_bus.emit(
                    ResourceRemovedEvent(resource_id=resource_id)
                )
            else:
                logger.warning(f"Failed to remove resource {resource_id}: {result.message}")
            return result
        except Exception as e:
            logger.error(f"Error removing resource {resource_id}: {e}")
            return OperationResult.error(f"Failed to remove resource: {str(e)}")

    async def get_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """
        Retrieve statistics for the user.

        Args:
            user_context: User context for the operation

        Returns:
            Dictionary containing user statistics
        """
        try:
            stats = await self._storage.get_user_statistics(user_context)
            logger.debug(f"Retrieved statistics for user {user_context.user_id}")
            return stats
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {}

    # =========================================================================
    # Sync Operations (extends ICoreService)
    # =========================================================================

    async def sync_sources(
        self,
        user_context: UserContext,
        sources: Optional[List[str]] = None,
    ) -> OperationResult[Dict[str, Any]]:
        """
        Synchronize content from configured sources.

        This method orchestrates the full sync process:
        1. Fetch content from sources
        2. Analyze with AI
        3. Store new resources

        Args:
            user_context: User context for the operation
            sources: Optional list of specific sources to sync (None = all)

        Returns:
            OperationResult with sync statistics
        """
        if self._content is None:
            return OperationResult.error("Content service not configured")

        # Get sources to sync
        sync_sources = sources if sources else self._config.sources

        if not sync_sources:
            return OperationResult.error("No sources configured for sync")

        sync_stats = {
            "total_sources": len(sync_sources),
            "processed": 0,
            "new_resources": 0,
            "errors": [],
        }

        logger.info(f"Starting sync for {len(sync_sources)} sources")

        # Emit sync started event
        from aisignal.core.events import Event

        self._event_bus.emit(Event(type=EventType.SYNC_STARTED))

        for i, source_url in enumerate(sync_sources):
            try:
                # Emit progress event - fetching
                self._event_bus.emit(
                    SyncProgressEvent(
                        source_url=source_url,
                        phase="fetching",
                        progress=(i / len(sync_sources)),
                        message=f"Fetching {source_url}",
                    )
                )

                # Fetch content
                content_result = await self._content.fetch_content(source_url)

                if content_result is None:
                    sync_stats["errors"].append(
                        {"source": source_url, "error": "Failed to fetch content"}
                    )
                    continue

                # Check if there's new content
                if not content_result.get("diff"):
                    logger.debug(f"No new content for {source_url}")
                    sync_stats["processed"] += 1
                    continue

                # Emit progress event - analyzing
                self._event_bus.emit(
                    SyncProgressEvent(
                        source_url=source_url,
                        phase="analyzing",
                        progress=((i + 0.5) / len(sync_sources)),
                        message=f"Analyzing {source_url}",
                    )
                )

                # Analyze content
                analysis_results = await self._content.analyze_content(
                    content_result, self._config.content_extraction_prompt
                )

                # Process and store resources
                if source_url in analysis_results:
                    items = analysis_results[source_url]
                    resources = self._items_to_resources(user_context, items, source_url)

                    if resources:
                        store_result = await self._storage.store_resources(
                            user_context, resources
                        )
                        if store_result.is_success:
                            sync_stats["new_resources"] += len(resources)

                sync_stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error syncing source {source_url}: {e}")
                sync_stats["errors"].append({"source": source_url, "error": str(e)})

        logger.info(
            f"Sync completed: {sync_stats['processed']}/{sync_stats['total_sources']} sources, "
            f"{sync_stats['new_resources']} new resources"
        )

        # Emit sync completed event
        self._event_bus.emit(
            SyncCompletedEvent(
                total_sources=sync_stats["total_sources"],
                processed_sources=sync_stats["processed"],
                new_resources=sync_stats["new_resources"],
                errors=[e["error"] for e in sync_stats["errors"]],
            )
        )

        return OperationResult.success(
            data=sync_stats,
            message=f"Synced {sync_stats['processed']} sources, found {sync_stats['new_resources']} new resources",
        )

    def _items_to_resources(
        self,
        user_context: UserContext,
        items: List[Dict],
        source_url: str,
    ) -> List[Resource]:
        """
        Convert analyzed items to Resource objects.

        Args:
            user_context: User context for the operation
            items: List of analyzed item dictionaries
            source_url: Source URL these items came from

        Returns:
            List of Resource objects
        """
        import uuid
        from datetime import datetime

        resources = []
        min_threshold = self._config.min_threshold

        for item in items:
            # Skip items below minimum threshold
            ranking = item.get("ranking", 0)
            if ranking < min_threshold:
                continue

            resource = Resource(
                id=str(uuid.uuid4()),
                user_id=user_context.user_id,
                title=item.get("title", "Untitled"),
                url=item.get("url", ""),
                categories=item.get("categories", []),
                ranking=ranking,
                summary=item.get("summary", ""),
                full_content=item.get("full_content", ""),
                datetime=datetime.now(),
                source=source_url,
                removed=False,
                notes="",
            )
            resources.append(resource)

        return resources

    # =========================================================================
    # Configuration Shortcuts
    # =========================================================================

    def get_categories(self) -> List[str]:
        """Get configured categories."""
        return self._config.categories

    def get_sources(self) -> List[str]:
        """Get configured sources."""
        return self._config.sources

    def get_thresholds(self) -> Dict[str, float]:
        """Get configured thresholds."""
        return {
            "min": self._config.min_threshold,
            "max": self._config.max_threshold,
        }
