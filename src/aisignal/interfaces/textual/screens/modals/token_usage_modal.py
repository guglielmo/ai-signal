from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Label

if TYPE_CHECKING:
    from aisignal.app import ContentCuratorApp


class TokenUsageModal(ModalScreen[None]):
    """
    Modal screen displaying token usage statistics.
    Shows both current session and total historical usage for both Jina AI and OpenAI.
    """

    BINDINGS = [
        Binding("q", "app.pop_screen", "Close"),
        Binding("escape", "app.pop_screen", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Token Usage Statistics", classes="modal-title")

            with Container():
                # Session usage
                yield Label("Current Session", classes="section-header")
                session_table = DataTable(id="session_usage")
                session_table.add_columns("Service", "Tokens", "Cost ($)")
                yield session_table

                # Historical usage
                yield Label("Historical Usage", classes="section-header")
                total_table = DataTable(id="total_usage")
                total_table.add_columns("Service", "Tokens", "Cost ($)")
                yield total_table

            yield Footer()

    def on_mount(self) -> None:
        """Update tables with current token usage data"""
        app = cast("ContentCuratorApp", self.app)
        session_usage = app.token_tracker.get_session_usage()
        total_usage = app.token_tracker.get_total_usage()

        # Current session table
        session_table = self.query_one("#session_usage", DataTable)
        session_table.clear()
        session_table.add_row(
            "Jina AI",
            f"{session_usage.jina_tokens:,}",
            f"${session_usage.jina_cost:.6f}",
        )
        session_table.add_row(
            "OpenAI (Input)",
            f"{session_usage.openai_input_tokens:,}",
            f"${session_usage.openai_input_cost:.6f}",
        )
        session_table.add_row(
            "OpenAI (Output)",
            f"{session_usage.openai_output_tokens:,}",
            f"${session_usage.openai_output_cost:.6f}",
        )

        session_total_tokens = (
            session_usage.jina_tokens
            + session_usage.openai_input_tokens
            + session_usage.openai_output_tokens
        )
        session_table.add_row(
            "Total",
            f"""{session_total_tokens:,}
            """,
            f"${session_usage.cost:.6f}",
        )

        # Historical usage table
        total_table = self.query_one("#total_usage", DataTable)
        total_table.clear()
        total_table.add_row(
            "Jina AI", f"{total_usage.jina_tokens:,}", f"${total_usage.jina_cost:.6f}"
        )
        total_table.add_row(
            "OpenAI (Input)",
            f"{total_usage.openai_input_tokens:,}",
            f"${total_usage.openai_input_cost:.6f}",
        )
        total_table.add_row(
            "OpenAI (Output)",
            f"{total_usage.openai_output_tokens:,}",
            f"${total_usage.openai_output_cost:.6f}",
        )
        historical_total_tokens = (
            total_usage.jina_tokens
            + total_usage.openai_input_tokens
            + total_usage.openai_output_tokens
        )
        total_table.add_row(
            "Total",
            f"""{historical_total_tokens:,}
            """,
            f"${total_usage.cost:.6f}",
        )
