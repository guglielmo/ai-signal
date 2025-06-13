from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header

if TYPE_CHECKING:
    from aisignal.app import ContentCuratorApp


class BaseScreen(Screen):
    """
    A base class for screens, providing foundational layout elements like
    header and footer, while requiring subclasses to define the main content
    area.
    """

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
