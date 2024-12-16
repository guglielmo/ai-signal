import asyncio
from datetime import datetime
from typing import cast

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Label, ListItem, ListView, ProgressBar

from aisignal.core.models import Resource
from aisignal.screens import BaseScreen
from aisignal.screens.config import ConfigScreen
from aisignal.screens.resource.detail import ResourceDetailScreen


class MainScreen(BaseScreen):
    """
    MainScreen is a user interface component that provides the primary display and
    interaction capabilities for managing resources within the application. It is
    responsible for displaying lists of resources in a data table, managing
    interactive filters for categories and sources, and handling synchronization
    processes. MainScreen utilizes a sidebar for managing filters and a main content
    area that displays the resources available through the application.
    """

    BINDINGS = [
        Binding("d", "delete", "Delete Resource"),
        Binding("s", "toggle_sort", "Toggle sort"),
        Binding("f", "sync", "Fetch content"),
        Binding("b", "toggle_filters", "Toggle sidebar"),
        Binding("c", "toggle_config", "Config"),
        Binding("r", "reset_filters", "Reset Filters"),
        Binding("q", "quit", "Quit application"),
    ]

    def __init__(self):
        super().__init__()
        self.is_syncing = False
        self._filters_active = False
        self._last_selected_row = None

    def compose_content(self) -> ComposeResult:
        """
        Generates the layout for the user interface, including a sidebar on the left and
          main content area. The sidebar contains filters and synchronization status,
          while the main content area displays a list of resources.

        :return: ComposeResult for the UI layout.
        """
        with Container():
            with Horizontal():
                # Left sidebar
                with Container(id="sidebar"):
                    yield Label("Categories")
                    yield ListView(id="category_filter")
                    yield Label("Sources")
                    yield ListView(id="source_filter")
                    with Container(id="sync_status"):
                        yield ProgressBar(id="sync_progress", show_eta=False)

                # Main content
                with Vertical(id="main_content"):
                    yield DataTable(id="resource_list")

    def on_mount(self) -> None:
        """
        Called when the main screen is mounted. This method performs initial setup
        and configuration tasks, including resource list initialization and setting
        up filters. It ensures that the main screen components are ready for user
        interaction.

        In particular, it initializes a data table for resource listing with specific
        columns and cursor type for row selection. It also sets up filters and updates
        the resource list to reflect any pre-existing data or state.

        :return: None
        """
        self.app.log.debug("Main screen mounted")
        # Initialize resource list
        table = self.query_one("#resource_list", DataTable)
        table.cursor_type = "row"
        table.add_columns("Title", "Source", "Categories", "Ranking", "Date")

        # hide progress bar
        progress = self.query_one("#sync_progress", ProgressBar)
        progress.styles.visibility = "hidden"

        # Initialize filters
        self._setup_filters()

        # Load existing items from storage
        self._load_stored_items()

        # Update resource list with loaded items
        self.update_resource_list()

        # give the focus to the data table
        table.focus()

    def _on_screen_resume(self) -> None:
        """Called when main screen becomes active again after being suspended"""
        super()._on_screen_resume()
        if self._last_selected_row:
            table = self.query_one("#resource_list", DataTable)
            latest_position = table.get_row_index(self._last_selected_row)
            self.update_resource_list(cursor_position=latest_position)

    def _load_stored_items(self) -> None:
        """
        Loads stored items from configured sources, processes them into Resource
        objects, and adds them to the application's resource manager. It retrieves
        stored items from the parsed item storage, attempts to convert each item
        into a Resource object, and handles any exceptions encountered during the
        conversion process.

        Exceptions during Resource creation are logged, and processing continues
        with remaining items.

        :return: None
        """
        storage = self.app.item_storage  # Assuming this exists
        resources = []

        for source in self.app.config_manager.sources:
            items = storage.get_stored_items(source)
            for item in items:
                try:
                    resource = Resource(
                        id=item["id"],
                        title=item["title"],
                        url=item["link"],
                        categories=item["categories"],
                        ranking=item["ranking"],
                        summary=item["summary"],
                        full_content=item["full_content"],
                        datetime=datetime.fromisoformat(item["first_seen"]),
                        source=item["source_url"],
                    )
                    resources.append(resource)
                except Exception as e:
                    self.app.log.error(f"Error creating resource from item: {e}")
                    continue

        self.app.resource_manager.add_resources(resources)

    def _setup_filters(self) -> None:
        """
        Sets up the available filters for categories and sources in the UI. This method
        queries and clears the current items in the category and source filter views.
        It then iterates through the list of categories and sources configured in the
        application, creates ListItem objects for each, and appends them to the
        corresponding ListView. If any of the categories or sources are already
        selected in the filter state, they are marked with a "-selected" class.

        :return: None
        """
        category_list = self.query_one("#category_filter", ListView)
        source_list = self.query_one("#source_filter", ListView)

        category_list.clear()
        source_list.clear()

        for category in self.app.config_manager.categories:
            item = ListItem(Label(category))
            if category in self.app.filter_state.selected_categories:
                item.add_class("-selected")
            category_list.append(item)

        for url in self.app.config_manager.sources:
            item = ListItem(Label(url))
            if url in self.app.filter_state.selected_sources:
                item.add_class("-selected")
            source_list.append(item)

    def _update_filter_state(self) -> None:
        """Update the visual indicators for active filters"""
        has_active_filters = bool(self.app.filter_state.selected_categories) or bool(
            self.app.filter_state.selected_sources
        )

        if has_active_filters != self._filters_active:
            self._filters_active = has_active_filters

            # Update filter section headers to show active state
            cat_label = self.query_one("Label:contains('Categories')", Label)
            src_label = self.query_one("Label:contains('Sources')", Label)

            if has_active_filters:
                cat_label.add_class("filters-active")
                src_label.add_class("filters-active")
            else:
                cat_label.remove_class("filters-active")
                src_label.remove_class("filters-active")

    def action_reset_filters(self) -> None:
        """Handle reset filters action from keyboard shortcut"""
        self.app.filter_state.reset()

        category_list = self.query_one("#category_filter", ListView)
        source_list = self.query_one("#source_filter", ListView)

        # Remove selection from all items
        for list_view in (category_list, source_list):
            for item in list_view.children:
                if item.has_class("-selected"):
                    item.remove_class("-selected")

        # Update the resource list with no filters
        self.update_resource_list()

        # Return focus to resource list
        self.query_one("#resource_list").focus()

        self.app.notify("Filters reset")

    def action_toggle_filters(self) -> None:
        """
        Toggles the visibility of the filters sidebar in the application. If the sidebar
        is currently hidden, it will be made visible with a width of 25%, and a
        notification will be displayed indicating that filters are visible. If the
        sidebar is visible, it will be hidden with a width of 0, and a notification will
        indicate that filters are hidden.

        :return: None
        """
        sidebar = self.query_one("#sidebar")
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
            sidebar.styles.width = "25%"
            self.app.notify("Filters visible")
        else:
            sidebar.add_class("-hidden")
            sidebar.styles.width = "0"
            self.app.notify("Filters hidden")

    def action_toggle_config(self) -> None:
        """
        Navigates the application to the configuration screen. This method triggers
        the transition to the `ConfigScreen`, allowing the user to view and modify
        configuration settings as needed.

        :return: None
        """
        self.app.push_screen(ConfigScreen())

    def action_toggle_sort(self) -> None:
        """Toggle sort order between ranking-first and datetime-first"""
        self.app.filter_state.toggle_sort()

        sort_mode = "datetime" if self.app.filter_state.sort_by_datetime else "ranking"
        self.app.notify(f"Sorting by {sort_mode} first")

    def action_delete(self) -> None:
        """Delete the currently highlighted resource."""
        table = self.query_one("#resource_list", DataTable)
        # Check if we have a highlighted row
        if table.cursor_row is not None:
            row_key = str(table.cursor_row)  # Get the key of highlighted row
            current_position = table.get_row_index(row_key)
            resource = self.app.resource_manager[row_key]
            # Mark as removed in storage and manager
            self.app.item_storage.mark_as_removed(resource.id)
            self.app.resource_manager.remove_resource(resource.id)

            # Update the UI
            self.app.notify(f"Removed resource: {resource.title}")
            self.update_resource_list(cursor_position=current_position)

    def action_sync(self) -> None:
        """
        Initiates the synchronization process if it is not already in progress.

        If the `is_syncing` attribute is False, this method creates an asynchronous
        task using `asyncio.create_task` to execute the `_sync_content` method.

        :return: None
        """
        if not self.is_syncing:
            asyncio.create_task(self._sync_content())

    def action_quit(self) -> None:
        """
        Exits the application by calling the exit method on the app instance.

        :return: None
        """
        self.app.exit()

    async def _sync_content(self) -> None:
        """
        Synchronizes content from configured sources, analyzes it,
        and updates the resource list in the application.

        Sets syncing status, updates progress, and processes content
        from configured sources via the content service.
        Analyzed items are compiled into resources and added to the resource manager.
        Handle errors during content analysis gracefully.

        :return: None
        """
        self.app.notify_user("Starting content synchronization")
        self.is_syncing = True
        progress = self.query_one("#sync_progress", ProgressBar)
        progress.styles.visibility = "visible"

        try:
            total_urls = len(self.app.config_manager.sources)
            progress.update(total=100)

            # Step 1: Fetch content from all sources
            content_results = []
            for i, url in enumerate(self.app.config_manager.sources):
                self.log.info(f"Processing source: {url}")

                self.log.info(" - Fetching markdown with Jina AI")
                content_result = await self.app.content_service.fetch_content(url)

                progress.advance((i + 1) / total_urls * 50)  # First 50% for fetching

                if not content_result:
                    self.app.handle_error(f"Failed to fetch content from {url}")
                    continue

                content_results.append(content_result)

            # Step 2: Batch analyze all content
            if content_results:
                self.log.info("Analyzing content with LLM")
                try:
                    config_manager = self.app.config_manager
                    analyzed_results = await self.app.content_service.analyze_content(
                        content_results,
                        prompt_template=config_manager.content_extraction_prompt,
                        # batch_size=config_manager.content_extraction_batch_size,
                        batch_size=3500,
                    )

                    # Step 3: Process analyzed results
                    min_threshold = self.app.content_service.min_threshold
                    new_resources = []
                    for url, items in analyzed_results.items():
                        # Last 50% for processing
                        if items == 0:
                            continue

                        progress.advance((len(new_resources) / len(items)) * 50 + 50)

                        for item in items:
                            try:
                                resource = Resource(
                                    id=str(len(new_resources)),
                                    title=item["title"],
                                    url=item["link"],
                                    categories=item["categories"],
                                    ranking=item["ranking"],
                                    summary=item["summary"],
                                    full_content=item.get("full_content", ""),
                                    datetime=datetime.fromisoformat(item["first_seen"]),
                                    source=item["source_url"],
                                )
                                if resource.ranking >= min_threshold:
                                    new_resources.append(resource)
                            except Exception as e:
                                self.app.log.error(
                                    f"Error creating resource: {item} {e}"
                                )
                                continue

                    if new_resources:
                        self.app.resource_manager.add_resources(new_resources)
                        self.update_resource_list()
                        self.app.notify_user(
                            f"Added {len(new_resources)} new resources"
                        )
                    else:
                        self.app.notify_user("No new resources found")

                except Exception as e:
                    self.app.handle_error("Error processing content", e)

        finally:
            self.is_syncing = False
            progress.styles.visibility = "hidden"
            progress.update(progress=0)
            self.update_resource_list()
            self.app.notify_user("Sync complete")

    def update_resource_list(self, cursor_position: int | None = None) -> None:
        """
        Updates the resource list displayed in the application by clearing the current
        data and repopulating it from the filtered resources. The function retrieves
        filtered resource entries from the resource manager, iterating through them
        to update the DataTable component with new rows. Each resource's details,
          such as title, source, categories, ranking, and date-time, are added to
          the table.

        In addition, the manager's row keys are updated to maintain the mapping
        between table rows and resource indices. After updating the table, the
        function logs the number of resources being displayed according to the
        applied filters.

        :return: None
        """
        table = self.query_one("#resource_list", DataTable)
        table.clear()

        self.app.resource_manager.clear_row_keys()

        # Get filtered resources
        filtered_resources = self.app.resource_manager.get_filtered_resources(
            categories=self.app.filter_state.selected_categories,
            sources=self.app.filter_state.selected_sources,
            sort_by_datetime=self.app.filter_state.sort_by_datetime,
        )
        self.app.resource_manager.filtered_resources = filtered_resources

        def get_color_style(ranking: float, has_full_content: bool = False) -> str:
            """Get text color based on ranking."""
            min_threshold = self.app.content_service.min_threshold
            max_threshold = self.app.content_service.max_threshold

            if ranking >= max_threshold:
                # Green color background for high quality
                color = "rgb(0,200,16)"
            elif ranking >= min_threshold:
                # Orange background for medium quality
                color = "rgb(255,176,0)"
            else:
                # Gray quality for low quality
                color = "rgb(100,100,100)"

            if has_full_content:
                color = f"{color} bold"

            return color

        def truncate_text(text: str, max_length: int = 50) -> str:
            """Truncates text to specified length, adding ellipsis if needed."""
            return text[:max_length] + "..." if len(text) > max_length else text

        # Update table
        for i, resource in enumerate(filtered_resources):
            ranking_color = get_color_style(resource.ranking, resource.full_content)
            row_key = table.add_row(
                Text(truncate_text(resource.title), style=ranking_color),
                Text(resource.source, style=ranking_color),
                Text(", ".join(resource.categories), style=ranking_color),
                Text(f"{resource.ranking:.2f}", style=ranking_color),
                Text(resource.datetime.strftime("%Y-%m-%d %H:%M"), style=ranking_color),
                key=str(i),
            )
            self.app.resource_manager.add_row_key(row_key, i)

        # At the end, after all rows have been added:
        if cursor_position is not None:
            # Ensure cursor_position is within bounds
            max_position = len(filtered_resources) - 1
            if max_position >= 0:
                cursor_position = min(cursor_position, max_position)
                table.move_cursor(row=cursor_position)

        # Log filter status
        self.log.debug(f"Showing {len(filtered_resources)} resources after filtering")
        self.log.debug(f"Moving the cursor at {cursor_position}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Handles the event triggered when a list view item is highlighted. The method
        receives an event of type `ListView.Highlighted` which contains details
        about the highlighted item in the list view.

        :param event: The event containing information about the highlighted item.
        :type event: ListView.Highlighted
        """
        list_view = event.list_view
        item = event.item
        label: Label = cast(Label, item.children[0])

        if list_view.id == "category_filter":
            category = label.renderable  # Get text from the Label widget
            self.app.filter_state.toggle_category(category)
            item.toggle_class("-selected")

        elif list_view.id == "source_filter":
            source = label.renderable
            self.app.filter_state.toggle_source(source)
            item.toggle_class("-selected")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handles the event triggered when a row in a data table is selected.

        This method logs the row key of the selected row and then retrieves the
        corresponding resource using the resource manager. It subsequently pushes a
        new screen to display details of the selected resource.

        :param event: The event object containing details about the selected row from
         the data table. The `row_key` attribute of the event denotes the identifier
         of the selected row.
        :return: None
        """
        self._last_selected_row = event.row_key
        self.app.log.info(event.row_key)
        resource = self.app.resource_manager[event.row_key]
        self.app.push_screen(ResourceDetailScreen(resource))
