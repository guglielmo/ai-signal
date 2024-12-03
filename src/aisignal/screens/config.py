from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer
from textual.reactive import Reactive
from textual.screen import Screen
from textual.widgets import Button, Input, Label, OptionList

from aisignal.screens import BaseScreen


class ConfigScreen(BaseScreen):
    """
    Represents a configuration screen allowing users to input and modify configuration
    settings such as API keys, categories, sources, and Obsidian-related paths.

    Attributes:
      BINDINGS: Defines key bindings for actions such as popping the screen and
        saving the configuration.
    """

    BINDINGS = [
        Binding("s", "save", "Save Config"),
        Binding("q", "app.pop_screen", "Close screen", show=True),
        Binding("escape", "app.pop_screen", "Close screen", show=True),
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
