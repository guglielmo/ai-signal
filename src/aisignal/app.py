from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding

from aisignal.core.filters import ResourceFilterState
from aisignal.services.storage import MarkdownSourceStorage, ParsedItemStorage

from .core.config import ConfigManager
from .core.export import ExportManager
from .core.resource_manager import ResourceManager
from .screens import MainScreen
from .services.content import ContentService


class ContentCuratorApp(App):
    """Main application class"""

    CSS_PATH = "styles/app.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()

        try:
            self.config_manager = ConfigManager(config_path)
            self.filter_state = ResourceFilterState(self.on_filter_change)
            self.resource_manager = ResourceManager()
            self.markdown_storage = MarkdownSourceStorage()
            self.item_storage = ParsedItemStorage()
            self.is_syncing = False
            self.content_service = ContentService(
                jina_api_key=self.config_manager.jina_api_key,
                openai_api_key=self.config_manager.openai_api_key,
                categories=self.config_manager.categories,
                markdown_storage=self.markdown_storage,
                item_storage=self.item_storage,
            )
            self.export_manager = ExportManager(
                self.config_manager.obsidian_vault_path,
                self.config_manager.obsidian_template_path,
            )
        except Exception as e:
            self.log.error(f"Failed to initialize app: {str(e)}")
            raise

    def on_mount(self) -> None:
        """Push the main screen when the app is mounted"""
        self.push_screen(MainScreen())

    def notify_user(self, message: str) -> None:
        """Display a notification to the user in the UI"""
        self.notify(message)

    def handle_error(self, message: str, error: Exception = None) -> None:
        """Log error and notify user"""
        error_msg = f"{message}: {str(error)}" if error else message
        self.log.error(error_msg)
        self.notify_user(f"Error: {message}")

    def on_filter_change(self) -> None:
        """Callback when filters change"""
        self.log("Filters updated, refreshing view")

        # Find the main screen and update its resource list
        main_screen = next(
            (s for s in self.screen_stack if isinstance(s, MainScreen)), None
        )
        if main_screen:
            main_screen.update_resource_list()


def run_app(config_path: Optional[Path] = None):
    """Run the application with optional config path"""
    app = ContentCuratorApp(config_path)
    app.run()


if __name__ == "__main__":
    run_app()
