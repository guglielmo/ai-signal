"""
Unified Storage Service Implementation

This module implements the IStorageService interface by wrapping and unifying
the existing MarkdownSourceStorage and ParsedItemStorage classes.
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from aisignal.core.interfaces import IStorageService
from aisignal.core.models import OperationResult, Resource, UserContext
from aisignal.services.storage import MarkdownSourceStorage, ParsedItemStorage


class StorageService(IStorageService):
    """
    Unified storage service that implements IStorageService by wrapping
    the existing MarkdownSourceStorage and ParsedItemStorage classes.

    This maintains backward compatibility while providing a clean interface
    for the core services.
    """

    def __init__(self, db_path: str = "storage.db"):
        """
        Initialize the storage service with existing storage classes.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.markdown_storage = MarkdownSourceStorage(db_path)
        self.parsed_storage = ParsedItemStorage(db_path)
        self._ensure_schema_updates()

    def _ensure_schema_updates(self):
        """
        Ensure the database schema has all required columns.
        This adds missing columns without breaking existing data.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check and add removed column if missing
            cursor.execute("PRAGMA table_info(items)")
            columns = [column[1] for column in cursor.fetchall()]

            if "removed" not in columns:
                cursor.execute("ALTER TABLE items ADD COLUMN removed INTEGER DEFAULT 0")

            if "notes" not in columns:
                cursor.execute("ALTER TABLE items ADD COLUMN notes TEXT DEFAULT ''")

            conn.commit()

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
        """
        Retrieve filtered resources for a user.
        """
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
            # Log error but return empty list to maintain compatibility
            return []

    async def get_resource_by_id(
        self, user_context: UserContext, resource_id: str
    ) -> Optional[Resource]:
        """
        Retrieve a specific resource by ID.
        """
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
        """
        Store a list of new resources.
        """
        try:
            # Convert resources to items format and use existing storage
            items_by_source = {}
            for resource in resources:
                source_url = resource.source
                if source_url not in items_by_source:
                    items_by_source[source_url] = []

                item = self._resource_to_item(resource)
                items_by_source[source_url].append(item)

            # Store items for each source
            for source_url, items in items_by_source.items():
                self.parsed_storage.store_items(source_url, items)

            return OperationResult.success(
                data=len(resources),
                message=f"Successfully stored {len(resources)} resources",
            )

        except Exception as e:
            return OperationResult.error(message=f"Failed to store resources: {str(e)}")

    async def update_resource(
        self, user_context: UserContext, resource_id: str, updates: Dict[str, Any]
    ) -> OperationResult:
        """
        Update an existing resource.
        """
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
        """
        Mark a resource as removed (soft delete).
        """
        try:
            self.parsed_storage.mark_as_removed(resource_id)
            return OperationResult.success(
                message=f"Resource {resource_id} marked as removed"
            )
        except Exception as e:
            return OperationResult.error(message=f"Failed to remove resource: {str(e)}")

    async def get_sources_content(
        self, user_context: UserContext, url: str
    ) -> Optional[str]:
        """
        Retrieve markdown content for a source URL.
        """
        try:
            return self.markdown_storage.get_stored_content(url)
        except Exception:
            return None

    async def store_source_content(
        self, user_context: UserContext, url: str, content: str
    ) -> OperationResult:
        """
        Store markdown content for a source URL.
        """
        try:
            self.markdown_storage.store_content(url, content)
            return OperationResult.success(message=f"Content stored for {url}")
        except Exception as e:
            return OperationResult.error(message=f"Failed to store content: {str(e)}")

    async def get_user_statistics(self, user_context: UserContext) -> Dict[str, Any]:
        """
        Retrieve statistics for a user.
        """
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

    def _item_to_resource(self, item: Dict[str, Any], user_id: str) -> Resource:
        """
        Convert a database item to a Resource object.
        """
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
        """
        Convert a Resource object to a database item format.
        Note: We don't include 'id' here because ParsedItemStorage generates it.
        """
        return {
            "title": resource.title,
            "link": resource.url,
            "categories": resource.categories,
            "summary": resource.summary,
            "full_content": resource.full_content,
            "ranking": resource.ranking,
        }

    def _get_generated_id(self, resource: Resource) -> str:
        """
        Get the ID that would be generated for a resource by ParsedItemStorage.
        This uses the same logic as ParsedItemStorage._get_item_identifier.
        """
        return hashlib.md5(f"{resource.url}{resource.title}".encode()).hexdigest()
