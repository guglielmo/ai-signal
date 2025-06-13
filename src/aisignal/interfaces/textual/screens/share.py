from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button

from aisignal.core.models import Resource
from aisignal.screens import BaseScreen


class ShareScreen(BaseScreen):
    """
    ShareScreen is responsible for displaying the screen that allows users
    to share content on social media platforms like Twitter and LinkedIn.

    :param resource: Resource object that holds the necessary data to be shared.
    """

    def __init__(self, resource: Resource):
        """
        Initializes the class with the given resource.

        :param resource: The resource object to be associated with this instance.
        :type resource: Resource
        """
        super().__init__()
        self.resource = resource

    def compose(self) -> ComposeResult:
        """
        Generates a composition result containing a container with buttons for sharing
        on social media platforms such as Twitter and LinkedIn.

        :return: An instance of ComposeResult containing a container with two buttons
         indicating social media sharing options.
        """
        yield Container(
            Button("Share on Twitter", id="twitter"),
            Button("Share on LinkedIn", id="linkedin"),
        )
