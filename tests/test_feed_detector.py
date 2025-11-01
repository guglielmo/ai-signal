"""
Tests for RSS/Atom feed detection utilities.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aisignal.utils.feed_detector import get_feed_type, is_feed


class TestFeedDetector:
    """Test suite for feed detection functions"""

    @pytest.mark.asyncio
    async def test_is_feed_with_valid_rss(self):
        """Test is_feed() with a valid RSS feed"""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test RSS Feed</title>
                <link>https://example.com</link>
                <description>A test RSS feed</description>
                <item>
                    <title>Test Item</title>
                    <link>https://example.com/item1</link>
                </item>
            </channel>
        </rss>"""

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            # Create mock response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=rss_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            # Create mock session
            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            # Configure the mock class to return our mock session
            mock_session_class.return_value = mock_session

            result = await is_feed("https://example.com/feed.xml")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_feed_with_valid_atom(self):
        """Test is_feed() with a valid Atom feed"""
        atom_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Atom Feed</title>
            <link href="https://example.com"/>
            <updated>2024-01-01T00:00:00Z</updated>
            <entry>
                <title>Test Entry</title>
                <link href="https://example.com/entry1"/>
                <updated>2024-01-01T00:00:00Z</updated>
            </entry>
        </feed>"""

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=atom_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await is_feed("https://example.com/atom.xml")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_feed_with_html_page(self):
        """Test is_feed() returns False for HTML pages"""
        html_content = """<!DOCTYPE html>
        <html>
            <head><title>Not a Feed</title></head>
            <body><h1>This is an HTML page</h1></body>
        </html>"""

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

            result = await is_feed("https://example.com/index.html")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_feed_with_404_error(self):
        """Test is_feed() handles 404 errors gracefully"""
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

            result = await is_feed("https://example.com/nonexistent.xml")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_feed_with_network_error(self):
        """Test is_feed() handles network errors gracefully"""
        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=Exception("Network error"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await is_feed("https://example.com/feed.xml")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_feed_type_with_rss(self):
        """Test get_feed_type() correctly identifies RSS feeds"""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>RSS Feed</title>
                <link>https://example.com</link>
            </channel>
        </rss>"""

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
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

            result = await get_feed_type("https://example.com/rss.xml")
            assert result == "rss"

    @pytest.mark.asyncio
    async def test_get_feed_type_with_atom(self):
        """Test get_feed_type() correctly identifies Atom feeds"""
        atom_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Atom Feed</title>
            <link href="https://example.com"/>
        </feed>"""

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=atom_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await get_feed_type("https://example.com/atom.xml")
            assert result == "atom"

    @pytest.mark.asyncio
    async def test_get_feed_type_with_html(self):
        """Test get_feed_type() returns None for HTML pages"""
        html_content = """<!DOCTYPE html>
        <html><body>Not a feed</body></html>"""

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

            result = await get_feed_type("https://example.com/index.html")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_feed_type_with_malformed_feed(self):
        """Test get_feed_type() handles malformed feeds gracefully"""
        malformed_content = """<?xml version="1.0"?>
        <notafeed>
            <invalid>content</invalid>
        </notafeed>"""

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=malformed_content)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await get_feed_type("https://example.com/bad.xml")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_feed_type_with_network_error(self):
        """Test get_feed_type() handles network errors gracefully"""
        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=Exception("Connection failed"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await get_feed_type("https://example.com/feed.xml")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_feed_type_with_timeout(self):
        """Test get_feed_type() handles timeout gracefully"""
        import asyncio

        with patch(
            "aisignal.utils.feed_detector.aiohttp.ClientSession"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session

            result = await get_feed_type("https://example.com/feed.xml")
            assert result is None
