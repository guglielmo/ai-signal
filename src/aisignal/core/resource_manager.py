from typing import Dict, List, Set

from textual import log

from .models import Resource


class ResourceManager:
    """
    Manages a collection of Resource objects, allowing for adding, accessing by
    row key, and filtering based on categories or sources.

    Attributes:
      resources (List[Resource]): List of resources managed by the instance.
      row_key_map (Dict[str, int]): Dictionary mapping row keys to resource indices.
    """

    def __init__(self):
        """
        Initializes a new instance of a class that manages resources and maintains a
        row key map.

        Attributes:
          resources (List[Resource]): A list to store Resource objects.
          row_key_map (Dict[str, int]): A dictionary to map row keys as strings
                                        to integer indices.
        """
        self.resources: List[Resource] = []
        self.filtered_resources: List[Resource] = []
        self.row_key_map: Dict[str, int] = {}  # DataTable row keys are strings

    def add_resources(self, resources: List[Resource]) -> None:
        """
        Adds new resources to the existing collection, preserving current resources.
        Clears row keys to ensure proper re-mapping.

        :param resources: List of Resource objects to be added.
        :return: None. The method updates the state of the object.
        """
        # Add only resources that aren't already present (based on id)
        existing_urls = {r.url for r in self.resources}
        filtered_resources = [r for r in resources if r.url not in existing_urls]

        # Extend the existing resources list
        self.resources.extend(filtered_resources)

        # Clear row keys for remapping
        self.clear_row_keys()

    def clear_row_keys(self) -> None:
        """
        Clears all entries from the row key map. This method removes all key-value
        pairs stored in `self.row_key_map`, effectively resetting it to an empty
        state.

        :return: None
        """
        self.row_key_map.clear()

    def add_row_key(self, row_key: str, resource_index: int) -> None:
        """
        Adds a mapping between a row key and a resource index to the instance's
        row_key_map dictionary.

        :param row_key: A string representing the key for a particular row.
        :param resource_index: An integer representing the index of the resource
          associated with the given row key.
        :return: None
        """
        self.row_key_map[row_key] = resource_index

    def __getitem__(self, row_key: str) -> Resource:
        """
        Retrieves the `Resource` associated with the given `row_key`.

        :param row_key: The key identifying the row whose associated `Resource`
          needs to be fetched.
        :return: The `Resource` object associated with the specified `row_key`.
        :raises KeyError: If the `row_key` does not exist in the row_key_map.
        """
        return self.filtered_resources[self.row_key_map[row_key]]

    def remove_resource(self, resource_id: str) -> None:
        """Remove resource from the list by marking it as removed"""
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
        """
        Filters resources based on specified categories and sources, and optionally
        sorts them by datetime.

        :param categories: A set of category names to filter resources by. Resources
         matching any of these categories will be included.
        :param sources: A set of source names to filter resources by. Resources
         matching any of these sources will be included.
        :param sort_by_datetime: If True, the result will be sorted by datetime in
         descending order. If False, the sorting will be based first on the date,
         then ranking, both in descending order.
        :return: A list of filtered and possibly sorted Resource objects.
        """
        filtered = [r for r in self.resources if not r.removed]
        log.debug(f"resources: {len(filtered)}")

        if categories:
            filtered = [
                r for r in filtered if any(c in categories for c in r.categories)
            ]

        if sources:
            filtered = [r for r in filtered if r.source in sources]

        # Sort results based on toggle
        if sort_by_datetime:
            return sorted(
                filtered, key=lambda r: (r.datetime.date(), r.ranking), reverse=True
            )
        else:
            return sorted(filtered, key=lambda r: (r.ranking, r.datetime), reverse=True)
