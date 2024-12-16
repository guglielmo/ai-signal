import difflib
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

from textual import log


@dataclass
class ContentDiff:
    """
    Represents the differences between two sets of content blocks, highlighting new
    additions and removals.

    Attributes:
      added_blocks (List[str]): A list of content blocks that have been added.
      removed_blocks (List[str]): A list of content blocks that have been removed.
      has_changes (bool): A flag indicating if there are any changes between the
        content sets.
    """

    added_blocks: List[str]  # New content blocks
    removed_blocks: List[str]  # Removed content blocks
    has_changes: bool


class MarkdownSourceStorage:
    """
    A class to handle the storage and comparison of markdown content in a
    SQLite database.
    """

    def __init__(self, db_path: str = "storage.db"):
        """
        Initializes an instance of MyClass with a specified database path.

        :param db_path: The file path for the database. Defaults to "storage.db".
        """
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """
        Initializes the database by creating a table named 'sources' if it does not
        already exist. The table schema includes the following columns:
        - url: TEXT, PRIMARY KEY, stores the URL of the source.
        - markdown_content: TEXT, NOT NULL, stores the markdown content of the source.
        - content_hash: TEXT, NOT NULL, stores the hash of the content for change
          detection.
        - last_updated: TIMESTAMP, NOT NULL, stores the timestamp of the last update.

        This method ensures that the database structure is established before any
        data operations are performed.

        :return: None
        """
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
        """
        Compares the stored content of a given URL with new content
        to determine changes.
        If no stored content is found, it assumes the content is entirely new.

        :param url: The URL of the source whose content needs to be compared.
        :type url: str
        :param new_content: The new markdown content to compare against stored content.
        :type new_content: str
        :return: An object containing lists of added and removed blocks of content,
          and a boolean indicating whether there are changes.
        :rtype: ContentDiff
        """
        # Retrieve stored content
        stored_content = self.get_stored_content(url)

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

    def get_stored_content(self, url: str) -> str:
        """
        Retrieves the stored content for a given URL from the database.

        :param url: The URL of the source whose content needs to be retrieved.
        :type url: str
        :return: The markdown content stored for the given URL, or None if not found.
        :rtype: str or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT markdown_content FROM sources WHERE url = ?", (url,))
            result = cursor.fetchone()
            return result[0] if result else None

    def store_content(self, url: str, content: str):
        """
        Stores the content in a SQLite database. The content is associated with the
        given URL and is stored along with a hash of the content and a timestamp of
        when it was last updated.

        :param url: The URL associated with the content.
        :param content: The content to be stored in the database.
        """
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

    @staticmethod
    def _split_into_blocks(content: Union[str | None]) -> List[str]:
        """
        Splits the given text content into a list of blocks, where each block is
        delimited by two newline characters. Each block in the resulting list is
        stripped of leading and trailing whitespace.

        :param content: The text content to be split into blocks.
        :return: A list of blocks with each block being a non-empty, stripped string.
        """
        if not content:
            return []
        return [b.strip() for b in content.split("\n\n") if b.strip()]


class ParsedItemStorage:
    """
    Class to manage storage of parsed items using SQLite.

    Attributes:
      db_path: The path to the SQLite database file.
    """

    def __init__(self, db_path: str = "storage.db"):
        """
        Initializes the StorageService class with a database path.

        :param db_path: The path to the database file. Defaults to "storage.db".
        """
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """
        Initializes the database by creating necessary tables and indexes. If the
        tables already exist, it does not recreate them. This method ensures that
        the 'items' table and its associated index are available for storing and
        querying item data.

        :raises sqlite3.Error: If an error occurs during the execution of SQL
          commands.
        :return: None
        """
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
                    ranking INTEGER NOT NULL DEFAULT 0,
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
        """
        Generates a unique identifier for a given item by creating an MD5 hash from
        the concatenation of the item's link and title.

        :param item: A dictionary that contains 'link' and 'title' keys. It represents
         the item for which the identifier should be generated.
        :return: A string representing the unique identifier of the item as an MD5
         hash.
        """
        return hashlib.md5(f"{item['link']}{item['title']}".encode()).hexdigest()

    def store_items(self, source_url: str, items: List[Dict]):
        """
        Stores a list of items into a SQLite database. Each item is checked for
        existence before insertion to avoid duplicates. Logs informative messages
        regarding the insertion success or errors encountered during the process.

        :param source_url: The URL from which the items were fetched.
        :type source_url: str
        :param items: A list of dictionaries, each containing details of an item
          such as 'title', 'link', 'categories', 'summary', and 'full_content'.
        :type items: List[Dict]
        """
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
                        summary, full_content, ranking)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            item["ranking"],
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
        """
        Retrieves stored items from the database that have a matching source URL,
        ordered by the 'first_seen' timestamp in descending order.

        :param source_url: URL of the source to filter items by.
        :return: A list of dictionaries where each dictionary represents an item
         with its attributes and parsed categories.
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM items 
                WHERE source_url = ? AND removed = 0
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
        """
        Filters out items that already exist in the database from the provided list
        based on the source URL and a unique item identifier.

        :param source_url: The URL source of the items being checked. Used to verify
         the origin of items in the database.
        :param items: A list of dictionaries representing the items to be filtered.
         Each dictionary should contain information sufficient to determine its
         uniqueness, typically an identifier.
        :return: A list of dictionaries representing items not found in the database,
         meaning they are new based on the criteria checked.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            new_items = []
            for item in items:
                item_id = self._get_item_identifier(item)

                cursor.execute(
                    """
                    SELECT 1 FROM items 
                    WHERE id = ? AND source_url = ? and removed = 0
                    LIMIT 1
                """,
                    (item_id, source_url),
                )

                if not cursor.fetchone():
                    new_items.append(item)

            return new_items

    def get_items_by_category(self, category: str) -> List[Dict]:
        """
        Fetches items from the database that belong to a specified category.

        :param category: The category to filter items by.
        :return: A list of dictionaries, where each dictionary represents an item
          and contains its details, including the categories it belongs to.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM items 
                WHERE json_extract(categories, '$[*]') LIKE ? and removed = 0
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

    def mark_as_removed(self, item_id: str) -> None:
        """Mark an item as removed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET removed = 1 WHERE id = ?", (item_id,))

    def update_note(self, item_id: str, note: str) -> None:
        """Update the note for an item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET notes = ? WHERE id = ?", (note, item_id))

    def update_full_content(self, item_id: str, content: str) -> None:
        """Update the full content of an item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE items SET full_content = ? WHERE id = ?", (content, item_id)
            )
