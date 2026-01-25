"""
Unit tests for RSS routing and auto-discovery functionality.

Tests the automatic feed detection, routing logic, and HTML feed discovery
implemented in Issues #17 and #18.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aisignal.core.services.content_service import ContentService
from aisignal.utils.feed_detector import discover_feeds


class TestFeedRouting:
    """Test automatic routing between RSS and HTML handlers."""

    @pytest.fixture
    def content_service(self):
        """Create a ContentService instance for testing."""
        storage = MagicMock()
        storage.get_content_diff = MagicMock(
            return_value=MagicMock(has_changes=True, added_blocks=[])
        )
        storage._store_content = MagicMock()

        token_tracker = MagicMock()
        token_tracker.estimate_jina_tokens = MagicMock(return_value=1000)
        token_tracker.add_jina_usage = MagicMock()

        service = ContentService(
            jina_api_key="test_key",
            openai_api_key="test_key",
            categories=["tech", "ai"],
            storage_service=storage,
            token_tracker=token_tracker,
            min_threshold=50,
            max_threshold=80,
        )
        return service

    @pytest.mark.asyncio
    async def test_direct_feed_routes_to_rss_parser(self, content_service):
        """Test that direct feed URLs route to RSS parser."""
        feed_url = "https://example.com/feed.xml"

        # Mock is_feed to return True
        with patch("aisignal.core.services.content_service.is_feed", return_value=True):
            # Mock fetch_rss_content to avoid actual network call
            with patch.object(
                content_service,
                "fetch_rss_content",
                return_value={
                    "url": feed_url,
                    "title": "Test Feed",
                    "content": "# Test\n\nContent",
                    "diff": MagicMock(has_changes=True),
                },
            ) as mock_rss:
                result = await content_service.fetch_content(feed_url)

                # Verify RSS handler was called
                mock_rss.assert_called_once_with(feed_url)
                assert result is not None
                assert result["url"] == feed_url

    @pytest.mark.asyncio
    async def test_html_with_discovered_feed_routes_to_rss_parser(
        self, content_service
    ):
        """Test that HTML pages with discoverable feeds route to RSS parser."""
        html_url = "https://blog.example.com"
        discovered_feed = "https://blog.example.com/feed.xml"

        # Mock is_feed to return False (not a direct feed)
        with patch(
            "aisignal.core.services.content_service.is_feed", return_value=False
        ):
            # Mock discover_feeds to return a feed URL
            with patch(
                "aisignal.core.services.content_service.discover_feeds",
                return_value=[discovered_feed],
            ):
                # Mock fetch_rss_content
                with patch.object(
                    content_service,
                    "fetch_rss_content",
                    return_value={
                        "url": discovered_feed,
                        "title": "Discovered Feed",
                        "content": "# Feed\n\nContent",
                        "diff": MagicMock(has_changes=True),
                    },
                ) as mock_rss:
                    result = await content_service.fetch_content(html_url)

                    # Verify RSS handler was called with discovered feed URL
                    mock_rss.assert_called_once_with(discovered_feed)
                    assert result is not None
                    assert result["url"] == discovered_feed

    @pytest.mark.asyncio
    async def test_html_without_feed_routes_to_jina(self, content_service):
        """Test that HTML pages without feeds route to Jina AI."""
        html_url = "https://example.com/article"

        # Mock is_feed to return False
        with patch(
            "aisignal.core.services.content_service.is_feed", return_value=False
        ):
            # Mock discover_feeds to return empty list (no feeds found)
            with patch(
                "aisignal.core.services.content_service.discover_feeds",
                return_value=[],
            ):
                # Mock _fetch_html_content
                with patch.object(
                    content_service,
                    "_fetch_html_content",
                    return_value={
                        "url": html_url,
                        "title": "HTML Article",
                        "content": "# Article\n\nContent",
                        "diff": MagicMock(has_changes=True),
                    },
                ) as mock_html:
                    result = await content_service.fetch_content(html_url)

                    # Verify Jina AI handler was called
                    mock_html.assert_called_once_with(html_url)
                    assert result is not None
                    assert result["url"] == html_url

    @pytest.mark.asyncio
    async def test_routing_uses_first_discovered_feed(self, content_service):
        """Test that routing uses the first discovered feed when multiple exist."""
        html_url = "https://blog.example.com"
        feeds = [
            "https://blog.example.com/feed.xml",
            "https://blog.example.com/atom.xml",
            "https://blog.example.com/rss.xml",
        ]

        with patch(
            "aisignal.core.services.content_service.is_feed", return_value=False
        ):
            with patch(
                "aisignal.core.services.content_service.discover_feeds",
                return_value=feeds,
            ):
                with patch.object(
                    content_service,
                    "fetch_rss_content",
                    return_value={
                        "url": feeds[0],
                        "title": "Feed",
                        "content": "Content",
                        "diff": MagicMock(has_changes=True),
                    },
                ) as mock_rss:
                    await content_service.fetch_content(html_url)

                    # Verify first feed was used
                    mock_rss.assert_called_once_with(feeds[0])


class TestFeedDiscovery:
    """Test HTML feed auto-discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_feeds_with_rss_link(self):
        """Test discovering RSS feed from HTML page."""
        html_content = """
        <html>
        <head>
            <link rel="alternate" type="application/rss+xml" href="/feed.xml">
        </head>
        <body>Blog content</body>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            assert len(feeds) == 1
            assert feeds[0] == "https://blog.example.com/feed.xml"

    @pytest.mark.asyncio
    async def test_discover_feeds_with_atom_link(self):
        """Test discovering Atom feed from HTML page."""
        html_content = """
        <html>
        <head>
            <link rel="alternate" type="application/atom+xml" href="/atom.xml">
        </head>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            assert len(feeds) == 1
            assert feeds[0] == "https://blog.example.com/atom.xml"

    @pytest.mark.asyncio
    async def test_discover_multiple_feeds(self):
        """Test discovering multiple feeds from HTML page."""
        html_content = """
        <html>
        <head>
            <link rel="alternate" type="application/rss+xml" href="/feed.xml">
            <link rel="alternate" type="application/atom+xml" href="/atom.xml">
        </head>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            assert len(feeds) == 2
            assert "https://blog.example.com/feed.xml" in feeds
            assert "https://blog.example.com/atom.xml" in feeds

    @pytest.mark.asyncio
    async def test_discover_feeds_handles_absolute_urls(self):
        """Test that absolute feed URLs are handled correctly."""
        html_content = """
        <html>
        <head>
            <link rel="alternate" type="application/rss+xml"
                  href="https://cdn.example.com/feeds/main.xml">
        </head>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            assert len(feeds) == 1
            assert feeds[0] == "https://cdn.example.com/feeds/main.xml"

    @pytest.mark.asyncio
    async def test_discover_feeds_handles_relative_paths(self):
        """Test that relative feed paths are converted to absolute URLs."""
        html_content = """
        <html>
        <head>
            <link rel="alternate" type="application/rss+xml" href="../feeds/blog.xml">
        </head>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com/posts/latest")

            assert len(feeds) == 1
            # urljoin should resolve relative path correctly
            assert "feeds/blog.xml" in feeds[0]

    @pytest.mark.asyncio
    async def test_discover_feeds_ignores_non_feed_links(self):
        """Test that non-feed link tags are ignored."""
        html_content = """
        <html>
        <head>
            <link rel="stylesheet" href="/style.css">
            <link rel="icon" href="/favicon.ico">
            <link rel="alternate" type="text/html" href="/mobile.html">
            <link rel="alternate" type="application/rss+xml" href="/feed.xml">
        </head>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            # Should only find the RSS feed, not other link types
            assert len(feeds) == 1
            assert feeds[0] == "https://blog.example.com/feed.xml"

    @pytest.mark.asyncio
    async def test_discover_feeds_returns_empty_on_404(self):
        """Test that discovery returns empty list on 404 error."""
        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://example.com/notfound")

            assert feeds == []

    @pytest.mark.asyncio
    async def test_discover_feeds_returns_empty_on_network_error(self):
        """Test that discovery returns empty list on network error."""
        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=Exception("Network error"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://example.com")

            assert feeds == []

    @pytest.mark.asyncio
    async def test_discover_feeds_returns_empty_when_no_feeds(self):
        """Test that discovery returns empty list when no feeds found."""
        html_content = """
        <html>
        <head>
            <title>Blog without feeds</title>
        </head>
        <body>Content</body>
        </html>
        """

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=html_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            feeds = await discover_feeds("https://blog.example.com")

            assert feeds == []
