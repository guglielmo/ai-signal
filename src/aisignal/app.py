from pathlib import Path
from typing import Iterable, Optional

from textual.app import App, SystemCommand
from textual.screen import Screen

from aisignal.core.filters import ResourceFilterState
from aisignal.core.token_tracker import TokenTracker
from aisignal.screens import TokenUsageModal
from aisignal.screens.main import MainScreen
from aisignal.services.storage import MarkdownSourceStorage, ParsedItemStorage

from .core.config import ConfigManager
from .core.export import ExportManager
from .core.resource_manager import ResourceManager
from .services.content import ContentService


class ContentCuratorApp(App):
    """
    Represents the main application for the content curation tool. It handles the
    initialization of various services and managers, and provides methods to manage
    UI components and error handling.

    Attributes:
      CSS_PATH (str): Path to the application's CSS file.
      BINDINGS (list): Key bindings for UI actions.

    Methods:
      on_mount: Pushes the main screen upon application mount.
      notify_user: Displays a notification to the user in the UI.
      handle_error: Logs errors and notifies the user.
      on_filter_change: Handles updates when filters change and refreshes the view.
    """

    CSS_PATH = "styles/app.tcss"
    COMMAND_PALETTE_BINDING = "slash"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initializes the application with necessary configurations and managers.

        :param config_path: Path to the configuration file. If not provided, default
          configuration is used.
        :raises Exception: If initialization of any component fails.
        """
        super().__init__()

        try:
            self.config_manager = ConfigManager(config_path)
            self.filter_state = ResourceFilterState(self.on_filter_change)
            self.resource_manager = ResourceManager()
            self.markdown_storage = MarkdownSourceStorage()
            self.item_storage = ParsedItemStorage()
            self.token_tracker = TokenTracker()
            self.is_syncing = False
            self.content_service = ContentService(
                jina_api_key=self.config_manager.jina_api_key,
                openai_api_key=self.config_manager.openai_api_key,
                categories=self.config_manager.categories,
                markdown_storage=self.markdown_storage,
                item_storage=self.item_storage,
                token_tracker=self.token_tracker,
                min_threshold=self.config_manager.min_threshold,
                max_threshold=self.config_manager.max_threshold,
            )
            self.export_manager = ExportManager(
                self.config_manager.obsidian_vault_path,
                self.config_manager.obsidian_template_path,
            )
        except Exception as e:
            self.log.error(f"Failed to initialize app: {str(e)}")
            raise

    def on_mount(self) -> None:
        """
        Invoked when the component is mounted in the UI hierarchy. Initializes the
        main screen by pushing it onto the screen stack.

        :return: None
        """
        self.push_screen(MainScreen())

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Add custom system commands to the command palette."""
        # Get the default system commands first
        yield from super().get_system_commands(screen)

        # Add token usage command
        yield SystemCommand(
            "Show Token Usage",
            "Display token usage statistics and costs",
            self.show_token_usage,
        )

    def show_token_usage(self) -> None:
        """Show the token usage modal when 't' is pressed"""
        self.app.push_screen(TokenUsageModal())

    def update_main_screen(self) -> None:
        """Find main screen in stack and update its resource list"""
        main_screen = next(
            (s for s in self.screen_stack if isinstance(s, MainScreen)), None
        )
        if main_screen:
            main_screen.update_resource_list()

    def notify_user(self, message: str) -> None:
        """
        Sends a notification message to the user.

        :param message: The message to be sent to the user.
        """
        self.notify(message)

    def handle_error(self, message: str, error: Exception = None) -> None:
        """
        Handles an error by logging an error message and notifying the user.

        :param message: A string detailing the error message to be logged and
         displayed to the user.
        :param error: An optional Exception object providing additional context
         about the error. If provided, its string representation is appended to
         the error message.
        :return: None
        """
        error_msg = f"{message}: {str(error)}" if error else message
        self.log.error(error_msg)
        self.notify_user(f"Error: {message}")

    def on_filter_change(self) -> None:
        """
        Handles changes to filter settings and ensures that the display is updated
        accordingly. It logs the filter update event and refreshes the view by
        updating the resource list in the main screen.

        This method identifies the main screen from the screen stack, which is
        expected to contain various screens including a main screen of type
        `MainScreen`. Upon finding the main screen, it invokes the method to
        refresh its resource list to reflect the updated filters.

        If no main screen is found, no action is taken beyond logging.

        :return: None
        """
        self.log("Filters updated, refreshing view")

        # Find the main screen and update its resource list
        main_screen = next(
            (s for s in self.screen_stack if isinstance(s, MainScreen)), None
        )
        if main_screen:
            main_screen.update_resource_list()


def run_app(config_path: Optional[Path] = None):
    """
    Initializes and runs the ContentCuratorApp application.

    :param config_path: Optional Path to the configuration file. If not provided,
      the application may use default settings.
    """
    app = ContentCuratorApp(config_path)
    app.run()


if __name__ == "__main__":
    run_app()
