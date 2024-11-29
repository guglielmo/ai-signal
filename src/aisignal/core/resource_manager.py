from typing import Dict, List, Set

from .models import Resource


class ResourceManager:
    def __init__(self):
        self.resources: List[Resource] = []
        self.row_key_map: Dict[str, int] = {}  # DataTable row keys are strings

    def add_resources(self, resources: List[Resource]) -> None:
        """Add new resources to the manager"""
        self.resources = resources
        self.clear_row_keys()

    def clear_row_keys(self) -> None:
        """Clear the row key mapping"""
        self.row_key_map.clear()

    def add_row_key(self, row_key: str, resource_index: int) -> None:
        """Map a DataTable row key to a resource index"""
        self.row_key_map[row_key] = resource_index

    def __getitem__(self, row_key: str) -> Resource:
        """Get a resource by its row key"""
        return self.resources[self.row_key_map[row_key]]

    def get_filtered_resources(
        self,
        categories: Set[str] = None,
        sources: Set[str] = None,
        sort_by_datetime: bool = False,
    ) -> List[Resource]:
        """Get resources filtered by categories and sources"""
        filtered = self.resources

        if categories:
            filtered = [
                r for r in filtered if any(c in categories for c in r.categories)
            ]

        if sources:
            filtered = [r for r in filtered if r.source in sources]

        # Sort results
        if sort_by_datetime:
            return sorted(filtered, key=lambda r: r.datetime, reverse=True)
        return sorted(
            filtered, key=lambda r: (r.datetime.date(), r.ranking), reverse=True
        )
