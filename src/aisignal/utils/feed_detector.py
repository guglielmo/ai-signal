"""
RSS/Atom feed detection utilities.

This module provides utility functions to detect if a URL points to an RSS or Atom
feed and to identify the specific feed type.
"""

from typing import Optional

import aiohttp
import feedparser


async def is_feed(url: str) -> bool:
    """
    Check if a URL points to a valid RSS or Atom feed.

    Args:
        url: The URL to check

    Returns:
        True if the URL points to a valid feed, False otherwise

    Examples:
        >>> await is_feed("https://blog.example.com/feed.xml")
        True
        >>> await is_feed("https://example.com/index.html")
        False
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return False

                content = await response.text()

        # Parse the content with feedparser
        feed = feedparser.parse(content)

        # Check if we got a valid feed with version info
        # This is the most reliable indicator
        if hasattr(feed, "version") and feed.version:
            return True

        # For well-formed feeds that might not have version set
        # check for feed structure (entries or channel)
        if feed.bozo == 0 and (hasattr(feed, "entries") and len(feed.entries) > 0):
            return True

        return False

    except (aiohttp.ClientError, TimeoutError, Exception):
        # Handle network failures and other errors gracefully
        return False


async def get_feed_type(url: str) -> Optional[str]:
    """
    Determine the type of feed at a given URL.

    Args:
        url: The URL to check

    Returns:
        'rss' for RSS feeds, 'atom' for Atom feeds, or None if not a valid feed

    Examples:
        >>> await get_feed_type("https://blog.example.com/rss.xml")
        'rss'
        >>> await get_feed_type("https://blog.example.com/atom.xml")
        'atom'
        >>> await get_feed_type("https://example.com/index.html")
        None
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return None

                content = await response.text()

        # Parse the content with feedparser
        feed = feedparser.parse(content)

        # Check if it's a valid feed first
        if feed.bozo == 1 and not (hasattr(feed, "version") and feed.version):
            return None

        # Determine feed type from version string
        if hasattr(feed, "version") and feed.version:
            version = feed.version.lower()

            # Atom feeds
            if "atom" in version:
                return "atom"

            # RSS feeds (includes rss 0.9x, rss 1.0, rss 2.0)
            if "rss" in version or version.startswith("rss"):
                return "rss"

            # CDF feeds (treated as RSS-like)
            if "cdf" in version:
                return "rss"

        return None

    except (aiohttp.ClientError, TimeoutError, Exception):
        # Handle network failures and other errors gracefully
        return None
