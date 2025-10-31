"""
Resource Manager Adapter for AI Signal Core.

This adapter wraps the existing ResourceManager to implement IResourceManager
interface without modifying the original implementation.
"""

from typing import List, Set

from aisignal.core.interfaces import IResourceManager
from aisignal.core.models import Resource
from aisignal.core.resource_manager import ResourceManager


class ResourceManagerAdapter(IResourceManager):
    """
    Adapter that wraps the existing ResourceManager to implement IResourceManager.

    This follows the Adapter pattern to make existing ResourceManager work
    with the new Core architecture without modifying the original class.
    """

    def __init__(self, resource_manager: ResourceManager):
        """
        Initialize adapter with existing ResourceManager instance.

        Args:
            resource_manager: Existing ResourceManager instance to wrap
        """
        self._resource_manager = resource_manager

    def add_resources(self, resources: List[Resource]) -> None:
        """
        Adds new resources to the existing collection, preserving current resources.

        Args:
            resources: List of Resource objects to be added.
        """
        self._resource_manager.add_resources(resources)

    def clear_row_keys(self) -> None:
        """
        Clears all entries from the row key map.
        """
        self._resource_manager.clear_row_keys()

    def add_row_key(self, row_key: str, resource_index: int) -> None:
        """
        Adds a mapping between a row key and a resource index.

        Args:
            row_key: A string representing the key for a particular row.
            resource_index: An integer representing the index of the resource.
        """
        self._resource_manager.add_row_key(row_key, resource_index)

    def __getitem__(self, row_key: str) -> Resource:
        """
        Retrieves the Resource associated with the given row_key.

        Args:
            row_key: The key identifying the row whose
            associated Resource needs to be fetched.

        Returns:
            The Resource object associated with the specified row_key.

        Raises:
            KeyError: If the row_key does not exist in the row_key_map.
        """
        return self._resource_manager[row_key]

    def remove_resource(self, resource_id: str) -> None:
        """
        Remove resource from the list by marking it as removed.

        Args:
            resource_id: The ID of the resource to remove.
        """
        self._resource_manager.remove_resource(resource_id)

    def get_filtered_resources(
        self,
        categories: Set[str] = None,
        sources: Set[str] = None,
        sort_by_datetime: bool = False,
    ) -> List[Resource]:
        """
        Filters resources based on specified categories and sources,
        and optionally sorts them.

        Args:
            categories: A set of category names to filter resources by.
            sources: A set of source names to filter resources by.
            sort_by_datetime: If True, sort by datetime in descending order.
                             If False, sort by ranking, then datetime.

        Returns:
            A list of filtered and possibly sorted Resource objects.
        """
        return self._resource_manager.get_filtered_resources(
            categories=categories, sources=sources, sort_by_datetime=sort_by_datetime
        )


# Factory function to create adapter from existing ResourceManager
def create_resource_adapter(
    resource_manager: ResourceManager = None,
) -> IResourceManager:
    """
    Factory function to create ResourceManagerAdapter.

    Args:
        resource_manager: Existing ResourceManager instance, creates new one if None

    Returns:
        IResourceManager implementation (ResourceManagerAdapter)
    """
    if resource_manager is None:
        resource_manager = ResourceManager()

    return ResourceManagerAdapter(resource_manager)
