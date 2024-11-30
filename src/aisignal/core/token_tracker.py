import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

COST_PER_MILLION = {
    "jina": 0.02,  # $0.02 per 1M tokens
    "openai_input": 0.15,  # $0.15 per 1M input tokens
    "openai_output": 0.60,  # $0.60 per 1M output tokens
}


@dataclass
class TokenUsage:
    """Represents token usage for a specific time period"""

    jina_tokens: int
    openai_input_tokens: int
    openai_output_tokens: int
    timestamp: datetime = datetime.now()

    @property
    def cost(self) -> float:
        """Calculate total cost in dollars"""
        return self.jina_cost + self.openai_cost

    @property
    def openai_cost(self) -> float:
        """Calculate OpenAI cost in dollars"""
        return self.openai_input_cost + self.openai_output_cost

    @property
    def openai_input_cost(self) -> float:
        return self.openai_input_tokens * COST_PER_MILLION["openai_input"] / 1_000_000

    @property
    def openai_output_cost(self) -> float:
        return self.openai_output_tokens * COST_PER_MILLION["openai_output"] / 1_000_000

    @property
    def jina_cost(self) -> float:
        """Calculate Jina cost in dollars"""
        return self.jina_tokens * COST_PER_MILLION["jina"] / 1_000_000


class TokenTracker:
    """
    Tracks and persists token usage across sessions
    """

    def __init__(self, db_path: str = "storage.db"):
        self.db_path = Path(db_path)
        self.session_jina_tokens = 0
        self.session_openai_input_tokens = 0
        self.session_openai_output_tokens = 0
        self.init_database()

    def init_database(self):
        """Initialize the database with token tracking table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jina_tokens INTEGER NOT NULL,
                    openai_input_tokens INTEGER NOT NULL,
                    openai_output_tokens INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """
            )
            conn.commit()

    @staticmethod
    def estimate_jina_tokens(text: str) -> int:
        """
        Estimate number of tokens in text for JinaAI pricing.
        Using a simple word-based estimation.

        :param text: Text to estimate tokens for
        :return: Estimated token count
        """
        words = len(text.split())
        return int(words * 1.3)  # rough approximation

    def add_jina_usage(self, text: str):
        """
        Record estimated JinaAI token usage based on text length

        :param text: Text returned from JinaAI
        """
        tokens = self.estimate_jina_tokens(text)
        self.session_jina_tokens += tokens
        self._persist_usage(tokens, 0, 0)

    def add_openai_usage(self, input_tokens: int, output_tokens: int):
        """
        Record OpenAI token usage

        :param input_tokens: Number of prompt tokens
        :param output_tokens: Number of completion tokens
        """
        self.session_openai_input_tokens += input_tokens
        self.session_openai_output_tokens += output_tokens
        self._persist_usage(0, input_tokens, output_tokens)

    def _persist_usage(self, jina: int, openai_input: int, openai_output: int):
        """Persist token usage to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO token_usage (
                    jina_tokens, 
                    openai_input_tokens, 
                    openai_output_tokens, 
                    timestamp
                )
                VALUES (?, ?, ?, ?)
                """,
                (jina, openai_input, openai_output, datetime.now().isoformat()),
            )
            conn.commit()

    def get_session_usage(self) -> TokenUsage:
        """Get token usage for current session"""
        return TokenUsage(
            jina_tokens=self.session_jina_tokens,
            openai_input_tokens=self.session_openai_input_tokens,
            openai_output_tokens=self.session_openai_output_tokens,
        )

    def get_total_usage(self) -> TokenUsage:
        """Get total token usage across all sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(jina_tokens), 0) as total_jina,
                    COALESCE(SUM(openai_input_tokens), 0) as total_openai_input,
                    COALESCE(SUM(openai_output_tokens), 0) as total_openai_output
                FROM token_usage
            """
            )
            total_jina, total_openai_input, total_openai_output = cursor.fetchone()
            return TokenUsage(
                jina_tokens=total_jina,
                openai_input_tokens=total_openai_input,
                openai_output_tokens=total_openai_output,
            )
