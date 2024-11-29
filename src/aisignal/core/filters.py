from dataclasses import dataclass
from typing import Callable, Set


@dataclass
class ResourceFilterState:
    """
    Represents the state of resource filtering, including selected categories,
    selected sources, and sorting preference. Notifies changes in filter state
    via a callback function.
    """

    selected_categories: Set[str]
    selected_sources: Set[str]
    sort_by_datetime: bool
    on_filter_change: Callable[[], None]

    def __init__(self, on_filter_change: Callable[[], None]):
        self.selected_categories = set()
        self.selected_sources = set()
        self.sort_by_datetime = False
        self.on_filter_change = on_filter_change

    def toggle_category(self, category: str) -> None:
        """Toggle a category selection"""
        if category in self.selected_categories:
            self.selected_categories.remove(category)
        else:
            self.selected_categories.add(category)
        self.on_filter_change()

    def toggle_source(self, source: str) -> None:
        """Toggle a source selection"""
        if source in self.selected_sources:
            self.selected_sources.remove(source)
        else:
            self.selected_sources.add(source)
        self.on_filter_change()

    def toggle_sort(self) -> None:
        """Toggle datetime sorting"""
        self.sort_by_datetime = not self.sort_by_datetime
        self.on_filter_change()

    def reset(self) -> None:
        """Reset all filters"""
        self.selected_categories.clear()
        self.selected_sources.clear()
        self.sort_by_datetime = False
        self.on_filter_change()
