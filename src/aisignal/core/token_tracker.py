import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TokenUsage:
    """Represents token usage for a specific time period"""

    jina_tokens: int
    openai_tokens: int
    timestamp: datetime = datetime.now()


class TokenTracker:
    """
    Tracks and persists token usage across sessions
    """

    def __init__(self, db_path: str = "storage.db"):
        self.db_path = Path(db_path)
        self.session_jina_tokens = 0
        self.session_openai_tokens = 0
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
                    openai_tokens INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """
            )
            conn.commit()

    def add_usage(self, jina_tokens: float, openai_tokens: int):
        """
        Record token usage both in session and persistent storage

        :param jina_tokens: Number of Jina AI tokens used
        :param openai_tokens: Number of OpenAI tokens used
        """
        # Update session totals
        self.session_jina_tokens += jina_tokens
        self.session_openai_tokens += openai_tokens

        # Persist to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO token_usage (jina_tokens, openai_tokens, timestamp)
                VALUES (?, ?, ?)
                """,
                (jina_tokens, openai_tokens, datetime.now().isoformat()),
            )
            conn.commit()

    def get_session_usage(self) -> TokenUsage:
        """Get token usage for current session"""
        return TokenUsage(
            jina_tokens=self.session_jina_tokens,
            openai_tokens=self.session_openai_tokens,
        )

    def get_total_usage(self) -> TokenUsage:
        """Get total token usage across all sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(jina_tokens), 0) as total_jina,
                    COALESCE(SUM(openai_tokens), 0) as total_openai
                FROM token_usage
            """
            )
            total_jina, total_openai = cursor.fetchone()
            return TokenUsage(jina_tokens=total_jina, openai_tokens=total_openai)
