from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import TextArea

from aisignal.core.models import Resource
from aisignal.screens import BaseScreen


class NoteInputModal(BaseScreen):
    """
    A modal screen for inputting and editing notes associated with a specific resource.

    Attributes:
      resource (Resource): The resource object with which the note is associated.

    Methods:
      compose: Sets up the text area for note input within the modal.
      action_save: Saves the note to the associated resource and closes the modal.
      action_cancel: Exits the modal without saving changes.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, resource: Resource):
        super().__init__()
        self.resource = resource

    def compose(self) -> ComposeResult:
        yield TextArea(self.resource.notes, id="note_input")

    def action_save(self) -> None:
        """Save the note and close modal."""
        note = self.query_one("#note_input").text
        self.app.item_storage.update_note(self.resource.id, note)
        self.app.notify("Note saved")
        self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel without saving."""
        self.app.pop_screen()
