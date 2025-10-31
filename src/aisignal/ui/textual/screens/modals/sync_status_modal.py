from textual import log
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Label, ProgressBar

from aisignal.core.sync_status import SyncProgress, SyncStatus


class SyncStatusModal(ModalScreen[None]):
    """Modal screen displaying sync progress status."""

    BINDINGS = [
        Binding("q", "app.pop_screen", "Close"),
        Binding("escape", "app.pop_screen", "Close"),
    ]

    def __init__(self, progress: SyncProgress = None):
        super().__init__()
        self.progress = progress

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Sync Status", classes="modal-title")

            with Container():
                yield ProgressBar(show_eta=False, id="sync_progress")
                yield DataTable(id="sync_details")

            yield Footer()

    def on_mount(self) -> None:
        """Set up the data table columns and start refresh timer"""
        table = self.query_one(DataTable)
        table.add_columns("Source", "Status", "Items", "New", "Error")
        # Set up periodic refresh
        self.set_interval(1, self.watch_progress)

    def watch_progress(self) -> None:
        """Update display when progress changes"""
        # Update progress bar
        progress_bar = self.query_one(ProgressBar)
        progress_bar.update(total=100, progress=self.progress.overall_progress)
        log.debug(f"Progress: {self.progress.overall_progress}")

        # Update status table
        table = self.query_one(DataTable)
        table.clear()

        for source in self.progress.sources.values():
            status_display = {
                SyncStatus.PENDING: "⏳",
                SyncStatus.IN_PROGRESS: "🔄",
                SyncStatus.COMPLETED: "✅",
                SyncStatus.FAILED: "❌",
            }.get(source.status, "")

            # Convert numeric values to strings or show "-" if no value
            items_count = str(source.items_found) if source.items_found > 0 else "-"
            new_items_count = str(source.new_items) if source.new_items > 0 else "-"
            error_text = source.error or "-"

            table.add_row(
                source.url, status_display, items_count, new_items_count, error_text
            )
