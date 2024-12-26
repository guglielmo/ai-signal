from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, ProgressBar, Static

from aisignal.core.sync_status import SyncProgress, SyncStatus


class SyncStatusWidget(Static):
    """Widget displaying sync progress and status"""

    progress: reactive[SyncProgress] = reactive[SyncProgress](SyncProgress())

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Sync Status", id="sync_header")
        yield ProgressBar(total=100, id="sync_progress")
        yield DataTable(id="sync_details")

    def on_mount(self) -> None:
        """Set up the data table columns"""
        table = self.query_one(DataTable)
        table.add_columns("Source", "Status", "Items", "New", "Error")
        # Set up periodic refresh
        self.set_interval(0.5, self.refresh_display)

    def refresh_display(self) -> None:
        """Refresh the display to show current progress"""
        if self.progress:
            self.watch_progress(self.progress)

    def watch_progress(self, progress: SyncProgress) -> None:
        """Update display when progress changes"""
        # Update progress bar
        progress_bar = self.query_one(ProgressBar)
        if progress.total_sources > 0:
            percent = (progress.completed_sources / progress.total_sources) * 100
            progress_bar.update(progress=percent)

        # Update status table
        table = self.query_one(DataTable)
        table.clear()

        for source in progress.sources.values():
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
