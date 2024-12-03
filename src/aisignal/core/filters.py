from dataclasses import dataclass
from typing import Callable, Set


@dataclass
class ResourceFilterState:
    """
    Represents the state of resource filters, including selected categories,
    selected sources, and a sorting flag. Provides methods to toggle states
    and reset all filters, triggering a callback function upon changes.
    """

    selected_categories: Set[str]
    selected_sources: Set[str]
    sort_by_datetime: bool
    on_filter_change: Callable[[], None]

    def __init__(self, on_filter_change: Callable[[], None]):
        self.selected_categories = set()
        self.selected_sources = set()
        self.sort_by_datetime = True
        self.on_filter_change = on_filter_change

    def toggle_category(self, category: str) -> None:
        """
        Toggles the presence of a given category in the selected categories set. If the
        category is currently in the set, it will be removed. If the category is
        absent, it will be added. Calls the on_filter_change method after updating
        the selected categories set.

        :param category: The category to toggle in the selected categories set.
        :type category: str
        """
        if category in self.selected_categories:
            self.selected_categories.remove(category)
        else:
            self.selected_categories.add(category)
        self.on_filter_change()

    def toggle_source(self, source: str) -> None:
        """
        Toggles the presence of a source in the selected_sources set. If the source
        is already present, it is removed. If it is not present, it is added. After
        modifying the selected_sources, it triggers the on_filter_change method to
        update any dependent state.

        :param source: The source to be toggled in the selected_sources set.
        :type source: str
        """
        if source in self.selected_sources:
            self.selected_sources.remove(source)
        else:
            self.selected_sources.add(source)
        self.on_filter_change()

    def toggle_sort(self) -> None:
        """
        Toggles between ranking-first and datetime-first sorting modes.
        When sort_by_datetime is True,
        resources are sorted by datetime first, then ranking.
        When False (default), resources are sorted by ranking first, then datetime.
        """
        self.sort_by_datetime = not self.sort_by_datetime
        self.on_filter_change()

    def reset(self) -> None:
        """
        Resets the filter settings to their default values. Clears the selected
        categories, selected sources, and sets the sorting by datetime to False.
        Triggers the on_filter_change callback to apply these settings.

        :return: None
        """
        self.selected_categories.clear()
        self.selected_sources.clear()
        self.sort_by_datetime = False
        self.on_filter_change()
