"""
RSS/Atom feed detection utilities.

This module provides utility functions to detect if a URL points to an RSS or Atom
feed and to identify the specific feed type. It also includes feed auto-discovery
from HTML pages.
"""

from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
import feedparser
from bs4 import BeautifulSoup


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


async def discover_feeds(url: str) -> List[str]:
    """
    Discover RSS/Atom feeds from an HTML page.

    Parses the HTML page for <link rel="alternate"> tags that point to feeds.
    Handles both relative and absolute URLs and returns feeds in priority order.

    Args:
        url: The URL of the HTML page to search

    Returns:
        List of discovered feed URLs (empty if none found or on error)

    Examples:
        >>> await discover_feeds("https://blog.example.com")
        ['https://blog.example.com/feed.xml', 'https://blog.example.com/atom.xml']
        >>> await discover_feeds("https://example.com/about")
        []
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return []

                html_content = await response.text()

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all link tags with rel="alternate"
        feed_links = []
        for link in soup.find_all("link", rel="alternate"):
            # Check if it's an RSS or Atom feed
            link_type = link.get("type", "").lower()
            href = link.get("href", "")

            if not href:
                continue

            # Only process RSS and Atom feeds
            if link_type in ["application/rss+xml", "application/atom+xml"]:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                feed_links.append(absolute_url)

        return feed_links

    except (aiohttp.ClientError, TimeoutError, Exception):
        # Handle network failures and other errors gracefully
        return []
