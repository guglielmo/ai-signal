"""
Unified Storage Service Implementation

This module implements the IStorageService interface by directly providing
storage functionality, replacing the existing MarkdownSourceStorage and
ParsedItemStorage classes.
"""

import difflib
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from textual import log

from aisignal.core.interfaces import IStorageService
from aisignal.core.models import OperationResult, Resource, UserContext


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


class StorageService(IStorageService):
    """
    Unified storage service that implements IStorageService by directly providing
    all storage functionality in one place.

    This replaces MarkdownSourceStorage and ParsedItemStorage with a single service.
    """

    def __init__(self, db_path: str = "storage.db"):
        """
        Initialize the storage service.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        """
        Initialize the database with all required tables.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create sources table for markdown content
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

            # Create items table for parsed content
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
                    removed INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    FOREIGN KEY (source_url) REFERENCES sources(url)
                )
            """
            )

            # Create index for faster source lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_items_source
                ON items(source_url)
            """
            )

            conn.commit()

    # =============================================================================
    # RESOURCE MANAGEMENT (implements IStorageService)
    # =============================================================================

    async def get_resources(
        self,
        user_context: UserContext,
        categories: Optional[Set[str]] = None,
        sources: Optional[Set[str]] = None,
        sort_by: str = "ranking",
        sort_desc: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Resource]:
        """Retrieve filtered resources for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build the query dynamically
                query = """
                SELECT * FROM items
                WHERE removed = 0
                """
                params = []

                # Filter by categories if specified
                if categories:
                    category_conditions = []
                    for category in categories:
                        category_conditions.append("categories LIKE ?")
                        params.append(f'%"{category}"%')
                    query += f" AND ({' OR '.join(category_conditions)})"

                # Filter by sources if specified
                if sources:
                    source_placeholders = ",".join("?" * len(sources))
                    query += f" AND source_url IN ({source_placeholders})"
                    params.extend(sources)

                # Add sorting
                sort_column = "ranking" if sort_by == "ranking" else "first_seen"
                sort_order = "DESC" if sort_desc else "ASC"
                query += f" ORDER BY {sort_column} {sort_order}"

                # Add pagination
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                if offset:
                    query += " OFFSET ?"
                    params.append(offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                resources = []
                for row in rows:
                    item = dict(row)
                    resource = self._item_to_resource(item, user_context.user_id)
                    resources.append(resource)

                return resources

        except Exception:
            return []

    async def get_resource_by_id(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """Retrieve a specific resource by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM items WHERE id = ? AND removed = 0", (resource_id,)
                )
                row = cursor.fetchone()

                if row:
                    item = dict(row)
                    return self._item_to_resource(item, user_context.user_id)

                return None

        except Exception:
            return None

    async def store_resources(
        self, user_context: UserContext, resources: List[Resource]
    ) -> OperationResult:
        """Store a list of new resources."""
        try:
            # Convert resources to items format and store them
            items_by_source = {}
            for resource in resources:
                source_url = resource.source
                if source_url not in items_by_source:
                    items_by_source[source_url] = []

                item = self._resource_to_item(resource)
                items_by_source[source_url].append(item)

            # Store items for each source
            for source_url, items in items_by_source.items():
                self._store_items(source_url, items)

            return OperationResult.success(
                data=len(resources),
                message=f"Successfully stored {len(resources)} resources",
            )

        except Exception as e:
            return OperationResult.error(message=f"Failed to store resources: {str(e)}")

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """Update an existing resource."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if resource exists
                cursor.execute(
                    "SELECT 1 FROM items WHERE id = ? AND removed = 0", (resource_id,)
                )
                if not cursor.fetchone():
                    return OperationResult.not_found(
                        f"Resource {resource_id} not found"
                    )

                # Build update query dynamically
                update_fields = []
                params = []

                for field, value in updates.items():
                    if field == "categories":
                        # Handle categories as JSON
                        update_fields.append("categories = ?")
                        params.append(json.dumps(value))
                    elif field in [
                        "title",
                        "summary",
                        "full_content",
                        "notes",
                        "ranking",
                    ]:
                        update_fields.append(f"{field} = ?")
                        params.append(value)

                if update_fields:
                    params.append(resource_id)
                    query = f"UPDATE items SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()

                return OperationResult.success(
                    message=f"Resource {resource_id} updated successfully"
                )

        except Exception as e:
            return OperationResult.error(message=f"Failed to update resource: {str(e)}")

    async def mark_resource_removed(
        self, user_context: UserContext, resource_id: str
    ) -> OperationResult:
        """Mark a resource as removed (soft delete)."""
        try:
            self._mark_as_removed(resource_id)
            return OperationResult.success(
                message=f"Resource {resource_id} marked as removed"
            )
        except Exception as e:
            return OperationResult.error(message=f"Failed to remove resource: {str(e)}")

    async def get_sources_content(
        self, user_context: UserContext, url: str
    ) -> Optional[str]:
        """Retrieve markdown content for a source URL."""
        try:
            return self._get_stored_content(url)
        except Exception:
            return None

    async def store_source_content(
        self, user_context: UserContext, url: str, content: str
    ) -> OperationResult:
        """Store markdown content for a source URL."""
        try:
            self._store_content(url, content)
            return OperationResult.success(message=f"Content stored for {url}")
        except Exception as e:
            return OperationResult.error(message=f"Failed to store content: {str(e)}")

    async def get_user_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """Retrieve statistics for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get basic statistics
                cursor.execute("SELECT COUNT(*) FROM items WHERE removed = 0")
                total_resources = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(DISTINCT source_url) FROM items WHERE removed = 0"
                )
                total_sources = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sources")
                total_source_content = cursor.fetchone()[0]

                return {
                    "total_resources": total_resources,
                    "total_sources": total_sources,
                    "total_source_content": total_source_content,
                    "user_id": user_context.user_id,
                }

        except Exception:
            return {
                "total_resources": 0,
                "total_sources": 0,
                "total_source_content": 0,
                "user_id": user_context.user_id,
            }

    # =============================================================================
    # LEGACY INTERFACE METHODS (for compatibility during migration)
    # =============================================================================

    def get_content_diff(self, url: str, new_content: str) -> ContentDiff:
        """Compare stored content with new content to determine changes."""
        # Retrieve stored content
        stored_content = self._get_stored_content(url)

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

    def get_stored_items(self, source_url: str) -> List[Dict]:
        """Retrieve stored items from the database for a source URL."""
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
        """Filter out items that already exist in the database."""
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
        """Fetch items from the database that belong to a specified category."""
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

    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================

    def _get_stored_content(self, url: str) -> str:
        """Retrieve stored content for a given URL from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT markdown_content FROM sources WHERE url = ?", (url,))
            result = cursor.fetchone()
            return result[0] if result else None

    def _store_content(self, url: str, content: str):
        """Store content in the database."""
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

    def _store_items(self, source_url: str, items: List[Dict]):
        """Store a list of items into the database."""
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
                            item.get("summary", ""),
                            item.get("full_content", ""),
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

    def _mark_as_removed(self, item_id: str) -> None:
        """Mark an item as removed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET removed = 1 WHERE id = ?", (item_id,))

    def _get_item_identifier(self, item: Dict) -> str:
        """Generate a unique identifier for an item."""
        return hashlib.md5(f"{item['link']}{item['title']}".encode()).hexdigest()

    @staticmethod
    def _split_into_blocks(content: Union[str | None]) -> List[str]:
        """Split content into blocks delimited by double newlines."""
        if not content:
            return []
        return [b.strip() for b in content.split("\\n\\n") if b.strip()]

    def _item_to_resource(self, item: Dict[str, Any], user_id: str) -> Resource:
        """Convert a database item to a Resource object."""
        # Parse categories from JSON
        categories = json.loads(item.get("categories", "[]"))

        # Handle datetime conversion
        datetime_str = item.get("first_seen")
        dt = datetime.fromisoformat(datetime_str) if datetime_str else datetime.now()

        return Resource(
            id=item["id"],
            user_id=user_id,
            title=item["title"],
            url=item["link"],
            categories=categories,
            ranking=float(item.get("ranking", 0)),
            summary=item.get("summary", ""),
            full_content=item.get("full_content", ""),
            datetime=dt,
            source=item["source_url"],
            removed=bool(item.get("removed", False)),
            notes=item.get("notes", ""),
        )

    def _resource_to_item(self, resource: Resource) -> Dict[str, Any]:
        """Convert a Resource object to a database item format."""
        return {
            "title": resource.title,
            "link": resource.url,
            "categories": resource.categories,
            "summary": resource.summary,
            "full_content": resource.full_content,
            "ranking": resource.ranking,
        }
