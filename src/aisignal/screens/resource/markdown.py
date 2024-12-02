from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import MarkdownViewer, Static

from aisignal.core.models import Resource
from aisignal.screens import BaseScreen
from aisignal.screens.resource.note import NoteInputModal


class ResourceMarkdownScreen(BaseScreen):
    """
    Class representing a screen displaying a markdown resource with various
    interactive actions.

    Attributes:
      BINDINGS: List of key bindings associated with actions for the screen.

    Methods:
      __init__(resource):
        Initializes the screen with a given resource.

      compose():
        Sets up the layout of the screen, including the title and markdown content.

      action_share():
        Placeholder action for sharing the resource. Currently, it notifies the
        user that the feature is not implemented.

      action_export_obsidian():
        Exports the resource to Obsidian using the app's export manager. Notifies
        the user upon success or failure.

      action_remove():
        Marks the resource as removed in the database and notifies the user.
        Navigates back to the previous screen.

      action_add_note():
        Opens a modal to add a note to the resource.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("s", "share", "Share"),
        Binding("o", "export_obsidian", "Export to Obsidian"),
        Binding("r", "remove", "Remove"),
        Binding("n", "add_note", "Add Note"),
    ]

    def __init__(self, resource: Resource):
        """Initialize with a resource."""
        super().__init__()
        self.resource = resource

    def compose_content(self) -> ComposeResult:
        """Create our layout."""
        with Vertical():
            yield Static(f"# {self.resource.title}", id="title")
            with ScrollableContainer():
                yield MarkdownViewer(
                    self.resource.full_content,
                    show_table_of_contents=True,
                    id="markdown_content",
                )

    def action_share(self) -> None:
        """Share the resource."""
        self.app.notify("Share functionality not implemented yet")

    def action_export_obsidian(self) -> None:
        """Export to Obsidian."""
        success, message = self.app.export_manager.export_to_obsidian(self.resource)
        self.app.notify(
            "Exported to Obsidian" if success else f"Export failed: {message}"
        )

    def action_remove(self) -> None:
        """Mark resource as removed."""
        # Update in database
        self.app.item_storage.mark_as_removed(self.resource.id)
        self.app.notify(f"Removed resource: {self.resource.title}")
        # Return to previous screen
        self.app.pop_screen()

    def action_add_note(self) -> None:
        """Add a note to the resource."""
        # Show note input modal
        self.app.push_screen(NoteInputModal(self.resource))
