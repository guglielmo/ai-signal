import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import Reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    OptionList,
    ProgressBar,
)

from aisignal.core.models import Resource

if TYPE_CHECKING:
    from .app import ContentCuratorApp


class BaseScreen(Screen):
    """
    A base class for creating screens, inheriting from the Screen class.
    Provides a framework for a consistent layout with a header and footer.
    """

    def compose(self) -> ComposeResult:
        """Base composition including header and footer"""
        yield Header()
        yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        """To be implemented by child screens"""
        yield Container()

    @property
    def app(self) -> "ContentCuratorApp":
        return super().app  # type: ignore


# Main screen containing the primary app functionality
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
        Binding("f", "toggle_filters", "Filters"),
        Binding("c", "toggle_config", "Config"),
        Binding("s", "sync", "Sync"),
    ]

    def __init__(self):
        super().__init__()
        self.is_syncing = False

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
        """Set up the screen when mounted"""
        self.app.log.debug("Main screen mounted")

        # Initialize resource list
        table = self.query_one("#resource_list", DataTable)
        table.cursor_type = "row"
        table.add_columns("Title", "Source", "Categories", "Ranking", "Date")

        # Initialize filters
        self._setup_filters()
        self.update_resource_list()

    def _setup_filters(self) -> None:
        """Setup category and source filters"""
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

    def action_toggle_filters(self) -> None:
        """Toggle visibility of the filters sidebar"""
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
        """Show configuration screen"""
        self.app.push_screen(ConfigScreen())

    def action_sync(self) -> None:
        """Start the synchronization process"""
        if not self.is_syncing:
            asyncio.create_task(self._sync_content())

    async def _sync_content(self) -> None:
        """
        Synchronizes content from various sources, analyzes it,
        and updates the resource list in the application.

        Sets syncing status, updates progress, and processes content
        from configured sources via the content service.
        Analyzed items are compiled into resources and added to the resource manager.
        Handle errors during content analysis gracefully.

        :return: None
        """
        self.log.info("Starting content synchronization")
        self.is_syncing = True
        progress = self.query_one("#sync_progress", ProgressBar)

        try:
            total_urls = len(self.app.config_manager.sources)
            progress.update(total=100)

            new_resources = []

            for i, url in enumerate(self.app.config_manager.sources):
                self.app.notify_user(f"Processing URL: {url}")
                progress.advance((i + 1) / total_urls * 100)

                content_result = await self.app.content_service.fetch_content(url)
                if not content_result:
                    self.app.handle_error(f"Failed to fetch content from {url}")
                    continue

                try:
                    items = await self.app.content_service.analyze_content(
                        content_result,
                        self.app.config_manager.content_extraction_prompt,
                    )

                    for item in items:
                        try:
                            resource = Resource(
                                id=str(len(new_resources)),
                                title=item["title"],
                                url=item["link"],
                                categories=item["categories"],
                                ranking=0.0,
                                summary=item["summary"],
                                full_content="",
                                datetime=datetime.strptime(
                                    item["first_seen"], "%Y-%m-%dT%H:%M:%S.%f"
                                ),
                                source=item["source_url"],
                            )
                            new_resources.append(resource)
                        except Exception as e:
                            self.app.log.error(f"Error: {item} {e}")
                            continue
                except Exception as e:
                    self.app.handle_error(f"Error processing content from {url}", e)
                    continue

            self.app.resource_manager.add_resources(new_resources)
            self.update_resource_list()
            self.app.notify_user(
                f"Sync completed. Added {len(new_resources)} resources"
            )
        finally:
            self.is_syncing = False
            progress.update(progress=0)

    def update_resource_list(self) -> None:
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

        # Update table
        for i, resource in enumerate(filtered_resources):
            row_key = table.add_row(
                resource.title,
                resource.source,
                ", ".join(resource.categories),
                f"{resource.ranking:.2f}",
                resource.datetime.strftime("%Y-%m-%d %H:%M"),
            )
            self.app.resource_manager.add_row_key(row_key, i)

        # Log filter status
        self.log(f"Showing {len(filtered_resources)} resources after filtering")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle list view highlight events"""
        # Implementation remains the same as in original app
        pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table"""

        self.app.log.info(event.row_key)
        resource = self.app.resource_manager[event.row_key]
        self.app.push_screen(ResourceDetailScreen(resource))


class ConfigScreen(BaseScreen):
    """Screen for viewing and editing configuration"""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("s", "save", "Save Config"),
    ]

    def compose_content(self) -> ComposeResult:
        with ScrollableContainer():
            yield Label("API Keys", classes="section-header")
            with Container(classes="section"):
                yield Label("JinaAI API Key")
                yield Input(
                    value=self.app.config_manager.jina_api_key,
                    password=True,
                    id="jina_api_key",
                )
                yield Label("OpenAI API Key")
                yield Input(
                    value=self.app.config_manager.openai_api_key,
                    password=True,
                    id="openai_api_key",
                )

            yield Label("Categories", classes="section-header")
            with Container(classes="section"):
                yield OptionList(
                    *self.app.config_manager.categories, id="categories"
                )
                yield Button("Add Category", id="add_category")

            yield Label("Sources", classes="section-header")
            with Container(classes="section"):
                yield OptionList(*self.app.config_manager.sources, id="sources")
                yield Button("Add Source", id="add_source")

            yield Label("Obsidian Settings", classes="section-header")
            with Container(classes="section"):
                yield Label("Vault Path")
                yield Input(
                    value=self.app.config_manager.obsidian_vault_path,
                    id="vault_path",
                )
                yield Label("Template Path")
                yield Input(
                    value=self.app.config_manager.obsidian_template_path or "",
                    id="template_path",
                )

    def action_save(self) -> None:
        """Save configuration changes"""
        try:
            # Collect values from inputs
            config = {
                "api_keys": {
                    "jinaai": self.query_one("#jina_api_key").value,
                    "openai": self.query_one("#openai_api_key").value,
                },
                "categories": [
                    item.label for item in self.query_one("#categories").options
                ],
                "sources": [item.label for item in self.query_one("#sources").options],
                "obsidian": {
                    "vault_path": self.query_one("#vault_path").value,
                    "template_path": self.query_one("#template_path").value or None,
                },
            }

            # Save configuration
            self.app.config_manager.save(config)
            self.notify("Configuration saved successfully")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Error saving configuration: {str(e)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "add_category":
            self.app.push_screen(
                AddItemScreen("Add Category", self.query_one("#categories").append)
            )
        elif event.button.id == "add_source":
            self.app.push_screen(
                AddItemScreen("Add Source", self.query_one("#sources").append)
            )


class ResourceDetailScreen(BaseScreen):
    """
    ResourceDetailScreen provides an interface to display detailed information about
    a resource. It offers functionalities to view, share, open in a browser, or export
    the resource data.

    Attributes:
      BINDINGS (list): A list of key bindings allowing user interactions, such as
        returning to the previous screen, opening the resource in a web browser,
        sharing the resource, or exporting it to the Obsidian application.
      resource (Resource): An instance of the Resource class containing information
        about the specific resource being displayed.

    Methods:
      __init__(resource):
        Initializes the ResourceDetailScreen with the given resource, setting up
        the display and interactions for the resource details.

      compose_content():
        Builds and displays the UI components for the resource's details, including
        the title, source, categories, ranking, date, a summary, and a portion of
        the full content. The summary and full content are presented conditionally
        based on their availability and length.

      action_open_browser():
        Opens the resource's URL in the default web browser, enabling quick access
        to the online content or detailed page related to the resource.

      action_share():
        Provides a placeholder for sharing functionality, notifying the user that
        sharing has not been implemented.

      action_export():
        Exports the resource details to the Obsidian application using the app's
        export manager, and informs the user upon successful export.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("o", "open_browser", "Open in Browser"),
        Binding("s", "share", "Share"),
        Binding("e", "export", "Export to Obsidian"),
    ]

    def __init__(self, resource: "Resource"):
        super().__init__()
        self.resource = resource

    def compose_content(self) -> ComposeResult:
        """Display the resource details"""
        with Vertical():
            yield Label(f"Title: {self.resource.title}")
            yield Label(f"Source: {self.resource.source}")
            yield Label(f"Categories: {', '.join(self.resource.categories)}")
            yield Label(f"Ranking: {self.resource.ranking:.2f}")
            yield Label(f"Date: {self.resource.datetime.strftime('%Y-%m-%d %H:%M')}")
            with Container():
                yield Label("Summary:")
                yield Label(
                    self.resource.summary
                    if self.resource.summary
                    else "No summary available"
                )
            with Container():
                yield Label("Content:")
                yield Label(
                    self.resource.full_content[:500] + "..."
                    if len(self.resource.full_content) > 500
                    else self.resource.full_content
                )

    def action_open_browser(self) -> None:
        """Open the resource URL in browser"""
        import webbrowser

        webbrowser.open(self.resource.url)

    def action_share(self) -> None:
        """Share the resource"""
        self.app.notify("Share functionality not implemented yet")

    def action_export(self) -> None:
        """Export to Obsidian"""
        self.app.export_manager.export_to_obsidian(self.resource)
        self.app.notify("Resource exported to Obsidian")


class ShareScreen(BaseScreen):
    """
    ShareScreen is responsible for displaying the screen that allows users
    to share content on social media platforms like Twitter and LinkedIn.

    :param resource: Resource object that holds the necessary data to be shared.
    """

    def __init__(self, resource: Resource):
        super().__init__()
        self.resource = resource

    def compose(self) -> ComposeResult:
        """
        Generates a composition result containing a container with buttons for sharing
        on social media platforms such as Twitter and LinkedIn.

        :return: An instance of ComposeResult containing a container with two buttons
         indicating social media sharing options.
        """
        yield Container(
            Button("Share on Twitter", id="twitter"),
            Button("Share on LinkedIn", id="linkedin"),
        )


class AddItemScreen(Screen):
    """Screen for adding a new item (category or source)"""

    def __init__(self, title: Reactive[str | None], callback) -> None:
        super().__init__()
        self.title = title
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.title),
            Input(id="new_item"),
            Button("Add", id="add"),
            Button("Cancel", id="cancel"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            new_item = self.query_one("#new_item").value
            if new_item:
                self.callback(new_item)
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()
