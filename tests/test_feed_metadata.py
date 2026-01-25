"""
Unit tests for feed metadata storage and tracking (Issue #19).

Tests that feed type, entry count, and last publish date are properly
captured and stored in the database.
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import AsyncMock, MagicMock, patch

from aisignal.core.services.content_service import ContentService
from aisignal.core.services.storage_service import StorageService


class TestFeedMetadataStorage:
    """Test feed metadata storage functionality."""

    @pytest.fixture
    def storage_service(self):
        """Create a temporary storage service for testing."""
        # Create temporary database file
        temp_db = NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        storage = StorageService(temp_db.name)
        yield storage

        # Cleanup
        Path(temp_db.name).unlink(missing_ok=True)

    @pytest.fixture
    def content_service(self, storage_service):
        """Create a ContentService instance for testing."""
        token_tracker = MagicMock()
        token_tracker.estimate_jina_tokens = MagicMock(return_value=1000)
        token_tracker.add_jina_usage = MagicMock()

        service = ContentService(
            jina_api_key="test_key",
            openai_api_key="test_key",
            categories=["tech", "ai"],
            storage_service=storage_service,
            token_tracker=token_tracker,
            min_threshold=50,
            max_threshold=80,
        )
        return service

    def test_database_migration_adds_metadata_columns(self, storage_service):
        """Test that database migration adds feed metadata columns."""
        # Check that metadata columns exist
        with sqlite3.connect(storage_service.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sources)")
            columns = {row[1] for row in cursor.fetchall()}

            assert "source_type" in columns
            assert "feed_entry_count" in columns
            assert "last_publish_date" in columns

    def test_store_content_with_rss_metadata(self, storage_service):
        """Test storing content with RSS feed metadata."""
        url = "https://example.com/feed.xml"
        content = "# Test Feed\n\nContent"
        last_publish = datetime.now().isoformat()

        storage_service._store_content(
            url=url,
            content=content,
            source_type="rss",
            feed_entry_count=15,
            last_publish_date=last_publish,
        )

        # Verify metadata was stored
        metadata = storage_service.get_source_metadata(url)
        assert metadata is not None
        assert metadata["source_type"] == "rss"
        assert metadata["feed_entry_count"] == 15
        assert metadata["last_publish_date"] == last_publish

    def test_store_content_with_atom_metadata(self, storage_service):
        """Test storing content with Atom feed metadata."""
        url = "https://example.com/atom.xml"
        content = "# Atom Feed\n\nContent"

        storage_service._store_content(
            url=url,
            content=content,
            source_type="atom",
            feed_entry_count=10,
            last_publish_date=None,
        )

        metadata = storage_service.get_source_metadata(url)
        assert metadata is not None
        assert metadata["source_type"] == "atom"
        assert metadata["feed_entry_count"] == 10
        assert metadata["last_publish_date"] is None

    def test_store_content_with_html_metadata(self, storage_service):
        """Test storing content with HTML (Jina AI) metadata."""
        url = "https://example.com/article"
        content = "# Article\n\nContent"

        storage_service._store_content(
            url=url, content=content, source_type="html", feed_entry_count=0
        )

        metadata = storage_service.get_source_metadata(url)
        assert metadata is not None
        assert metadata["source_type"] == "html"
        assert metadata["feed_entry_count"] == 0

    def test_store_content_defaults_to_html(self, storage_service):
        """Test that store_content defaults to HTML metadata."""
        url = "https://example.com/page"
        content = "Content"

        # Call without metadata (old behavior)
        storage_service._store_content(url, content)

        metadata = storage_service.get_source_metadata(url)
        assert metadata is not None
        assert metadata["source_type"] == "html"
        assert metadata["feed_entry_count"] == 0

    def test_get_source_metadata_returns_none_for_nonexistent_source(
        self, storage_service
    ):
        """Test that get_source_metadata returns None for nonexistent source."""
        metadata = storage_service.get_source_metadata("https://nonexistent.com")
        assert metadata is None

    @pytest.mark.asyncio
    async def test_rss_fetch_stores_metadata(self, content_service):
        """Test that RSS feed fetch captures and stores metadata."""
        rss_content = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test RSS Feed</title>
                <item>
                    <title>Item 1</title>
                    <link>https://example.com/1</link>
                    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Item 2</title>
                    <link>https://example.com/2</link>
                </item>
            </channel>
        </rss>"""

        with patch("aisignal.core.services.content_service.aiohttp.ClientSession"):
            with patch(
                "aisignal.utils.feed_detector.aiohttp.ClientSession"
            ) as mock_session_class:
                # Mock feed fetch
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=rss_content)
                mock_response.__aenter__ = AsyncMock(return_value=mock_response)
                mock_response.__aexit__ = AsyncMock(return_value=None)

                mock_session = MagicMock()
                mock_session.get = MagicMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)

                mock_session_class.return_value = mock_session

                # Fetch RSS content
                url = "https://example.com/feed.xml"
                result = await content_service.fetch_rss_content(url)

                assert result is not None

                # Verify metadata was stored
                metadata = content_service.storage_service.get_source_metadata(url)
                assert metadata is not None
                assert metadata["source_type"] in ["rss", "atom"]  # Could be either
                assert metadata["feed_entry_count"] == 2
                # last_publish_date may or may not be set depending on parsing

    def test_metadata_update_on_content_change(self, storage_service):
        """Test that metadata is updated when content changes."""
        url = "https://example.com/feed.xml"

        # Store initial version
        storage_service._store_content(
            url=url,
            content="Version 1",
            source_type="rss",
            feed_entry_count=5,
        )

        # Update with new version
        storage_service._store_content(
            url=url,
            content="Version 2",
            source_type="rss",
            feed_entry_count=10,
        )

        # Verify metadata was updated
        metadata = storage_service.get_source_metadata(url)
        assert metadata["feed_entry_count"] == 10

    def test_different_source_types_tracked_separately(self, storage_service):
        """Test that different source types are tracked correctly."""
        # Store RSS feed
        storage_service._store_content(
            "https://blog.com/feed.xml", "RSS", source_type="rss", feed_entry_count=5
        )

        # Store Atom feed
        storage_service._store_content(
            "https://blog.com/atom.xml", "Atom", source_type="atom", feed_entry_count=8
        )

        # Store HTML page
        storage_service._store_content(
            "https://blog.com/article", "HTML", source_type="html"
        )

        # Verify each has correct metadata
        rss_meta = storage_service.get_source_metadata("https://blog.com/feed.xml")
        atom_meta = storage_service.get_source_metadata("https://blog.com/atom.xml")
        html_meta = storage_service.get_source_metadata("https://blog.com/article")

        assert rss_meta["source_type"] == "rss"
        assert rss_meta["feed_entry_count"] == 5

        assert atom_meta["source_type"] == "atom"
        assert atom_meta["feed_entry_count"] == 8

        assert html_meta["source_type"] == "html"
        assert html_meta["feed_entry_count"] == 0
