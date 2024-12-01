import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import Reactive
from textual.screen import ModalScreen, Screen
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
    A base class for screens, providing foundational layout elements like
    header and footer, while requiring subclasses to define the main content
    area.
    """

    BINDINGS = [
        Binding("u", "show_token_usage", "Token Usage", priority=True),
    ]

    def compose(self) -> ComposeResult:
        """
        Composes and yields a series of UI components which include a header, content,
        and footer. The content is generated dynamically by the `compose_content`
        method, which is expected to yield its parts.

        Yields:
            Header: The static header component.
            Iteration[Component]: The components produced by `compose_content`.
            Footer: The static footer component.
        """
        yield Header()
        yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        """
        Generates and provides the content for composition.

        The `compose_content` method is designed to yield content
        that is contained within a `Container` object. It is utilized
        to define the structure or layout for the content composition.

        Yields:
          Container: An instance of `Container` that holds the composed
            elements or widgets.
        """
        yield Container()

    @property
    def app(self) -> "ContentCuratorApp":
        """
        Retrieves the ContentCuratorApp instance associated with the current object.

        This property overrides the base class implementation to return the specific
        application instance utilized within the content curation context.

        :return: The ContentCuratorApp instance for the current object.
        """
        return super().app  # type: ignore

    def action_show_token_usage(self) -> None:
        """Show the token usage modal when 't' is pressed"""
        self.app.push_screen(TokenUsageModal())


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
        Binding("r", "reset_filters", "Reset Filters"),  # New keyboard shortcut
    ]

    def __init__(self):
        super().__init__()
        self.is_syncing = False
        self._filters_active = False

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

    def action_sync(self) -> None:
        """
        Initiates the synchronization process if it is not already in progress.

        If the `is_syncing` attribute is False, this method creates an asynchronous
        task using `asyncio.create_task` to execute the `_sync_content` method.

        :return: None
        """
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
        progress.styles.visibility = "visible"

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
                                ranking=item["ranking"],
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

        finally:
            self.is_syncing = False
            progress.styles.visibility = "hidden"
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
        self.app.resource_manager.filtered_resources = filtered_resources

        def truncate_text(text: str, max_length: int = 50) -> str:
            """Truncates text to specified length, adding ellipsis if needed."""
            return text[:max_length] + "..." if len(text) > max_length else text

        # Update table
        for i, resource in enumerate(filtered_resources):
            row_key = table.add_row(
                truncate_text(resource.title),
                resource.source,
                ", ".join(resource.categories),
                f"{resource.ranking:.2f}",
                resource.datetime.strftime("%Y-%m-%d %H:%M"),
            )
            self.app.resource_manager.add_row_key(row_key, i)

        # Log filter status
        self.log(f"Showing {len(filtered_resources)} resources after filtering")

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

        self.app.log.info(event.row_key)
        resource = self.app.resource_manager[event.row_key]
        self.app.push_screen(ResourceDetailScreen(resource))


class ConfigScreen(BaseScreen):
    """
    Represents a configuration screen allowing users to input and modify configuration
    settings such as API keys, categories, sources, and Obsidian-related paths.

    Attributes:
      BINDINGS: Defines key bindings for actions such as popping the screen and
        saving the configuration.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("s", "save", "Save Config"),
    ]

    def compose_content(self) -> ComposeResult:
        """
        Compose the structure and content of the user interface for API keys,
        categories, sources, and Obsidian settings.
        This method generates the UI components needed for user input and
        configuration management.

        :return: A generator yielding UI components for
          each section of the configuration.
        """
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
                yield OptionList(*self.app.config_manager.categories, id="categories")
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
        """
        Saves the current configuration settings by collecting input values and storing
        them using the application's configuration manager. Notifies the user of success
        or failure during the save operation.

        :raises: Exception if there is an error in saving the configuration.
        """
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
        """
        Handles button press events. Depending on the button id, this function
        navigates to a relevant screen to add a category or source.

        :param event: The button press event containing information about
         the pressed button and related context.
        """
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
        """
        Initializes a new instance of the class.

        :param resource: An instance of the Resource class that the instance
          will manage. This parameter is stored as an instance attribute
          for use within the class.
        """
        super().__init__()
        self.resource = resource

    def compose_content(self) -> ComposeResult:
        """
        Generates a structured composition of content based on the internal resource
        data. The content includes details such as title, source, categories, ranking,
        date, summary, and a truncated version of the full content.

        Yields:
          ComposeResult: A structured representation consisting of labels
          displaying the resource attributes.
        """
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
        """
        Opens the URL stored in the resource object using the default web browser.

        Utilizes the `webbrowser` module to open the web page specified by the
        URL from the resource associated with the current instance.

        :return: None
        """
        import webbrowser

        webbrowser.open(self.resource.url)

    def action_share(self) -> None:
        """
        Displays a notification indicating that the share functionality is not
        yet implemented.

        This method triggers a notification within the application to inform
        users that the requested feature, share functionality, is currently
        unavailable. This serves as a placeholder action to prevent errors
        when the share request is triggered.

        :return: None
        """
        self.app.notify("Share functionality not implemented yet")

    def action_export(self) -> None:
        """
        Exports the current resource to Obsidian and notifies the application.

        Utilizes the export manager within the application to perform the
        export operation for the specified resource. Following the export
        operation, a notification message is sent to inform the user that
        the resource has been successfully exported to Obsidian.

        :return: None
        """
        self.app.export_manager.export_to_obsidian(self.resource)
        self.app.notify("Resource exported to Obsidian")


class ShareScreen(BaseScreen):
    """
    ShareScreen is responsible for displaying the screen that allows users
    to share content on social media platforms like Twitter and LinkedIn.

    :param resource: Resource object that holds the necessary data to be shared.
    """

    def __init__(self, resource: Resource):
        """
        Initializes the class with the given resource.

        :param resource: The resource object to be associated with this instance.
        :type resource: Resource
        """
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
    """
    A screen for adding a new item with a title, input, and action buttons.

    Attributes:
      title: A reactive string representing the screen title, modifiable by UI
        state changes.
      callback: A function to be called with the new item's value when the "Add"
        button is pressed.

    Methods:
      compose: Sets up the UI layout by adding title, input field, and buttons.
      on_button_pressed: Handles button press events to add an item or cancel
        the action.
    """

    def __init__(self, title: Reactive[str | None], callback) -> None:
        """
        Initializes a new instance of the class with a given title and callback.

        :param title: A reactive string that can be None. Represents the title
          of the instance.
        :param callback: A callable object that will be executed during the
          instance's lifecycle.
        """
        super().__init__()
        self.title = title
        self.callback = callback

    def compose(self) -> ComposeResult:
        """
        Generates and yields a container with user interface elements for adding
        new items. The container includes a label displaying the title, an input
        field for new item entry, and buttons for adding or canceling the operation.

        :return: A ComposeResult containing a container with label, input, and
        buttons for the user interface.
        """
        yield Container(
            Label(self.title),
            Input(id="new_item"),
            Button("Add", id="add"),
            Button("Cancel", id="cancel"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles the button pressed event. Depending on the button ID, it either adds
        a new item or cancels the action by popping the current screen.

        :param event: Button pressed event containing information about the button that
          was pressed.
        :return: None
        """
        if event.button.id == "add":
            new_item = self.query_one("#new_item").value
            if new_item:
                self.callback(new_item)
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()


class TokenUsageModal(ModalScreen[None]):
    """
    Modal screen displaying token usage statistics.
    Shows both current session and total historical usage for both Jina AI and OpenAI.
    """

    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Token Usage Statistics", classes="modal-title")

            with Container():
                # Session usage
                yield Label("Current Session", classes="section-header")
                session_table = DataTable(id="session_usage")
                session_table.add_columns("Service", "Tokens", "Cost ($)")
                yield session_table

                # Historical usage
                yield Label("Historical Usage", classes="section-header")
                total_table = DataTable(id="total_usage")
                total_table.add_columns("Service", "Tokens", "Cost ($)")
                yield total_table

            yield Footer()

    def on_mount(self) -> None:
        """Update tables with current token usage data"""
        app = cast("ContentCuratorApp", self.app)
        session_usage = app.token_tracker.get_session_usage()
        total_usage = app.token_tracker.get_total_usage()

        # Current session table
        session_table = self.query_one("#session_usage", DataTable)
        session_table.clear()
        session_table.add_row(
            "Jina AI",
            f"{session_usage.jina_tokens:,}",
            f"${session_usage.jina_cost:.6f}",
        )
        session_table.add_row(
            "OpenAI (Input)",
            f"{session_usage.openai_input_tokens:,}",
            f"${session_usage.openai_input_cost:.6f}",
        )
        session_table.add_row(
            "OpenAI (Output)",
            f"{session_usage.openai_output_tokens:,}",
            f"${session_usage.openai_output_cost:.6f}",
        )
        session_table.add_row(
            "Total",
            f"""{(session_usage.jina_tokens + 
                session_usage.openai_input_tokens + 
                session_usage.openai_output_tokens):,}
            """,
            f"${session_usage.cost:.6f}",
        )

        # Historical usage table
        total_table = self.query_one("#total_usage", DataTable)
        total_table.clear()
        total_table.add_row(
            "Jina AI", f"{total_usage.jina_tokens:,}", f"${total_usage.jina_cost:.6f}"
        )
        total_table.add_row(
            "OpenAI (Input)",
            f"{total_usage.openai_input_tokens:,}",
            f"${total_usage.openai_input_cost:.6f}",
        )
        total_table.add_row(
            "OpenAI (Output)",
            f"{total_usage.openai_output_tokens:,}",
            f"${total_usage.openai_output_cost:.6f}",
        )
        total_table.add_row(
            "Total",
            f"""{
                total_usage.jina_tokens + 
                total_usage.openai_input_tokens + 
                total_usage.openai_output_tokens:,}
            """,
            f"${total_usage.cost:.6f}",
        )
