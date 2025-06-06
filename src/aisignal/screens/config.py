import yaml
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, TextArea

from aisignal.screens import BaseScreen


class ConfigScreen(BaseScreen):
    """
    Represents a configuration screen allowing users to edit the configuration
    file as raw YAML text in a text editor with syntax validation.

    Attributes:
      BINDINGS: Defines key bindings for actions such as popping the screen and
        saving the configuration.
    """

    BINDINGS = [
        Binding(key="ctrl+s", action="save", description="Save Config", show=True),
        Binding(
            key="ctrl+q", action="app.pop_screen", description="Close screen", show=True
        ),
    ]

    def compose_content(self) -> ComposeResult:
        """
        Compose the structure and content of the user interface for editing
        the configuration file as raw YAML text.

        :return: A generator yielding UI components for the text-based editor.
        """
        with Vertical():
            yield Label("Configuration Editor", classes="section-header")
            yield TextArea(id="config_editor", language="yaml")
            with Horizontal(classes="button-row"):
                yield Button("Save", id="save_config", variant="primary")
                yield Button("Cancel", id="cancel_config")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Load the raw YAML configuration content into the text area
        config_path = self.app.config_manager.config_path
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config_content = f.read()
            else:
                # If config doesn't exist, show a default template
                config_content = """api_keys:
  jinaai: ""
  openai: ""

categories: []
sources: []

obsidian:
  vault_path: ""
  template_path: null

sync_interval: 24
min_threshold: 0.0
max_threshold: 100.0

prompts:
  content_extraction: ""
"""

            self.query_one("#config_editor").text = config_content
            # Focus the text editor to allow immediate typing
            self.query_one("#config_editor").focus()
        except Exception as e:
            self.notify(f"Error loading configuration: {str(e)}")
            self.query_one("#config_editor").text = "# Error loading configuration"

    def action_save(self) -> None:
        """
        Saves the configuration by validating YAML syntax and writing to file.
        Shows success message and closes screen if valid, or error message if invalid.
        """
        self._save_config()

    def _save_config(self) -> None:
        """
        Validates and saves the YAML configuration from the text editor.
        """
        try:
            # Get the YAML content from the text editor
            config_content = self.query_one("#config_editor").text

            # Validate YAML syntax
            try:
                yaml.safe_load(config_content)
            except yaml.YAMLError as e:
                self.notify(f"YAML syntax error: {str(e)}")
                return

            # Write the content directly to the config file
            config_path = self.app.config_manager.config_path
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w") as f:
                f.write(config_content)

            # Reload the configuration manager's config
            self.app.config_manager.config = self.app.config_manager._load_config()

            self.notify("Configuration saved successfully")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Error saving configuration: {str(e)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles button press events for Save and Cancel buttons.

        :param event: The button press event containing information about
         the pressed button and related context.
        """
        if event.button.id == "save_config":
            self._save_config()
        elif event.button.id == "cancel_config":
            self.app.pop_screen()
