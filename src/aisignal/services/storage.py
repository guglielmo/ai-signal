import difflib
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from textual import log


@dataclass
class ContentDiff:
    """Represents differences between old and new content"""

    added_blocks: List[str]  # New content blocks
    removed_blocks: List[str]  # Removed content blocks
    has_changes: bool


class MarkdownSourceStorage:
    """Stores and manages markdown content from sources using SQLite"""

    def __init__(self, db_path: str = "storage.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Store markdown sources
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    url TEXT PRIMARY KEY,
                    markdown_content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_updated TIMESTAMP NOT NULL
                )
            """
            )

            conn.commit()

    def get_content_diff(self, url: str, new_content: str) -> ContentDiff:
        """Compare new content with stored version and identify changes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get stored content
            cursor.execute("SELECT markdown_content FROM sources WHERE url = ?", (url,))
            result = cursor.fetchone()

            if not result:
                # First time seeing this source
                return ContentDiff(
                    added_blocks=self._split_into_blocks(new_content),
                    removed_blocks=[],
                    has_changes=True,
                )

            stored_content = result[0]

            # Split both contents into blocks
            old_blocks = self._split_into_blocks(stored_content)
            new_blocks = self._split_into_blocks(new_content)

            # Use difflib for intelligent difference detection
            differ = difflib.Differ()
            diff = list(differ.compare(old_blocks, new_blocks))

            added = []
            removed = []

            for line in diff:
                if line.startswith("+ "):
                    added.append(line[2:])
                elif line.startswith("- "):
                    removed.append(line[2:])

            return ContentDiff(
                added_blocks=added,
                removed_blocks=removed,
                has_changes=bool(added or removed),
            )

    def store_content(self, url: str, content: str):
        """Store new content version"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sources 
                (url, markdown_content, content_hash, last_updated)
                VALUES (?, ?, ?, ?)
            """,
                (url, content, content_hash, datetime.now().isoformat()),
            )

    def _split_into_blocks(self, content: str) -> List[str]:
        """Split content into logical blocks for diffing"""
        return [b.strip() for b in content.split("\n\n") if b.strip()]


class ParsedItemStorage:
    """Stores and manages parsed items using SQLite"""

    def __init__(self, db_path: str = "storage.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Store items
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    first_seen TIMESTAMP NOT NULL,
                    categories TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    full_content TEXT NOT NULL,
                    FOREIGN KEY (source_url) REFERENCES sources(url)
                )
            """
            )

            # Index for faster source lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_items_source 
                ON items(source_url)
            """
            )

            conn.commit()

    def _get_item_identifier(self, item: Dict) -> str:
        """Create a unique identifier for an item"""
        return hashlib.md5(f"{item['link']}{item['title']}".encode()).hexdigest()

    def store_items(self, source_url: str, items: List[Dict]):
        """Store new items for a source"""
        current_time = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for item in items:
                item_id = self._get_item_identifier(item)
                categories_json = json.dumps(item["categories"])

                try:
                    # First check if item exists
                    cursor.execute("SELECT 1 FROM items WHERE id = ?", (item_id,))
                    if cursor.fetchone():
                        log.info(f"Item {item_id} already exists, skipping")
                        continue

                    cursor.execute(
                        """
                        INSERT INTO items 
                        (id, source_url, title, link, first_seen, categories, 
                        summary, full_content)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            item_id,
                            source_url,
                            item["title"],
                            item["link"],
                            current_time,
                            categories_json,
                            item.get("summary", ""),  # Use get() with default
                            item.get("full_content", ""),  # Use get() with default
                        ),
                    )

                    # Verify the insert
                    if cursor.rowcount == 1:
                        log.info(f"Successfully stored item {item_id} for {source_url}")
                    else:
                        log.warning(f"Insert appeared to fail for item {item_id}")

                except sqlite3.Error as e:
                    log.error(f"SQLite error storing item {item_id}: {e}")
                except Exception as e:
                    log.error(f"Unexpected error storing item {item_id}: {e}")

            # Commit at the end of all inserts
            try:
                conn.commit()
                log.info(f"Committed {len(items)} items to database")
            except sqlite3.Error as e:
                log.error(f"Error committing transaction: {e}")

    def get_stored_items(self, source_url: str) -> List[Dict]:
        """Retrieve all stored items for a source"""

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM items 
                WHERE source_url = ?
                ORDER BY first_seen DESC
            """,
                (source_url,),
            )

            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse categories from JSON
                item["categories"] = json.loads(item["categories"])
                items.append(item)

            return items

    def filter_new_items(self, source_url: str, items: List[Dict]) -> List[Dict]:
        """Filter out items that have already been stored"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            new_items = []
            for item in items:
                item_id = self._get_item_identifier(item)

                cursor.execute(
                    """
                    SELECT 1 FROM items 
                    WHERE id = ? AND source_url = ?
                    LIMIT 1
                """,
                    (item_id, source_url),
                )

                if not cursor.fetchone():
                    new_items.append(item)

            return new_items

    def get_items_by_category(self, category: str) -> List[Dict]:
        """Query items by category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM items 
                WHERE json_extract(categories, '$[*]') LIKE ?
                ORDER BY first_seen DESC
            """,
                (f"%{category}%",),
            )

            items = []
            for row in cursor.fetchall():
                item = dict(row)
                item["categories"] = json.loads(item["categories"])
                items.append(item)

            return items
