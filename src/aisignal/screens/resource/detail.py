import asyncio

from textual.app import ComposeResult
from textual.binding import BindingsMap
from textual.containers import Container, Vertical
from textual.widgets import Label, LoadingIndicator, MarkdownViewer

from aisignal.core.models import Resource
from aisignal.screens import BaseScreen


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

    def __init__(self, resource: "Resource"):
        """
        Initializes a new instance of the class.

        :param resource: An instance of the Resource class that the instance
          will manage. This parameter is stored as an instance attribute
          for use within the class.
        """
        super().__init__()
        self.resource = resource
        self.is_high_quality = (
            resource.ranking >= self.app.content_service.max_threshold
        )

    def update_bindings_for_content(self):
        new_bindings = BindingsMap()

        # Always present bindings
        new_bindings.bind("d", "delete", "Delete")
        new_bindings.bind("o", "export", "-> Obsidian")
        # new_bindings.bind("s", "share", "Share")

        if not self.resource.full_content:
            new_bindings.bind("f", "fetch_full", "Fetch Full Content")
        else:
            new_bindings.bind("f", "fetch_full", "Re-fetch Full Content")

        new_bindings.bind("q", "app.pop_screen", "Close screen")
        new_bindings.bind("escape", "app.pop_screen", "Close screen")

        self._bindings = new_bindings

    def compose_content(self) -> ComposeResult:
        """
        Generates a structured composition of content based on the internal resource
        data. The content includes details such as title, source, categories, ranking,
        date, summary, and a truncated version of the full content.

        Yields:
          ComposeResult: A structured representation consisting of labels
          displaying the resource attributes.
        """

        self.update_bindings_for_content()

        with Vertical():
            with Container(id="header_info"):
                yield Label(f"Title: {self.resource.title}")
                yield Label(f"Source: {self.resource.source}")
                yield Label(f"Link: {self.resource.url}")
                yield Label(f"Categories: {', '.join(self.resource.categories)}")
                yield Label(f"Ranking: {self.resource.ranking:.2f}")
                yield Label(
                    f"Date: {self.resource.datetime.strftime('%Y-%m-%d %H:%M')}"
                )

            with Container(id="content_container"):
                if self.resource.full_content:
                    with Container():
                        yield MarkdownViewer(
                            self.resource.full_content,
                            show_table_of_contents=True,
                            id="markdown_content",
                        )
                else:
                    yield Label(
                        self.resource.summary
                        if self.resource.summary
                        else "No summary available"
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

    def action_fetch_full(self) -> None:
        """Fetch full content and switch to markdown view."""
        self.app.notify("Fetching full content...")
        asyncio.create_task(self._fetch_full_content())

    async def _fetch_full_content(self) -> None:
        """Fetch full content and update view."""

        # Show loading indicator
        loading = LoadingIndicator()
        await self.mount(loading)

        try:
            content = await self.app.content_service.fetch_full_content(
                self.resource.url
            )
            if content:
                self.resource.full_content = content
                # Update in database
                self.app.item_storage.update_full_content(self.resource.id, content)

                # Remove all existing widgets
                await loading.remove()
                await self.query("*").remove()

                # Manually rebuild the screen structure
                vertical = Vertical()
                await self.mount(vertical)

                # Header info
                header_info = Container(id="header_info")
                await vertical.mount(header_info)
                await header_info.mount(Label(f"Title: {self.resource.title}"))
                await header_info.mount(Label(f"Source: {self.resource.source}"))
                await header_info.mount(Label(f"Link: {self.resource.url}"))
                await header_info.mount(
                    Label(f"Categories: {', '.join(self.resource.categories)}")
                )
                await header_info.mount(Label(f"Ranking: {self.resource.ranking:.2f}"))
                await header_info.mount(
                    Label(f"Date: {self.resource.datetime.strftime('%Y-%m-%d %H:%M')}")
                )

                # Content container
                content_container = Container(id="content_container")
                await vertical.mount(content_container)
                markdown_viewer = MarkdownViewer(
                    self.resource.full_content,
                    show_table_of_contents=True,
                    id="markdown_content",
                )
                await content_container.mount(markdown_viewer)

                # Focus handling
                async def ensure_markdown_focus():
                    # Give the UI a moment to stabilize
                    await asyncio.sleep(0.1)
                    if markdown_viewer := self.query_one(
                        "#markdown_content", MarkdownViewer
                    ):
                        self.set_focus(None)  # Clear any existing focus
                        markdown_viewer.can_focus = True
                        markdown_viewer.scroll_home()  # Ensure we're at the top
                        markdown_viewer.focus()
                        self.app.notify("Markdown viewer focused")  # Debug notification

                # Schedule the focus handling
                asyncio.create_task(ensure_markdown_focus())

                # Update bindings since content is now available
                self.update_bindings_for_content()
            else:
                self.app.notify("Failed to fetch full content")
        finally:
            await loading.remove()

    def action_delete(self) -> None:
        """Mark resource as removed."""
        self.app.item_storage.mark_as_removed(self.resource.id)
        self.app.resource_manager.remove_resource(self.resource.id)
        self.app.notify(f"Removed resource: {self.resource.title}")
        self.app.update_main_screen()
        self.app.pop_screen()
