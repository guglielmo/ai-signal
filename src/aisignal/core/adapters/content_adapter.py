"""
Content Service Adapter for AI Signal Core.

This adapter wraps the existing ContentService to implement IContentService
interface without modifying the original implementation.
"""

from typing import Dict, List, Optional, Union

from aisignal.core.interfaces import IContentService
from aisignal.services.content import ContentService


class ContentServiceAdapter(IContentService):
    """
    Adapter that wraps the existing ContentService to implement IContentService.

    This follows the Adapter pattern to make existing ContentService work
    with the new Core architecture without modifying the original class.
    """

    def __init__(self, content_service: ContentService):
        """
        Initialize adapter with existing ContentService instance.

        Args:
            content_service: Existing ContentService instance to wrap
        """
        self._content_service = content_service

    async def fetch_content(self, url: str) -> Optional[Dict]:
        """
        Fetch content from URL and compare with stored version.

        Args:
            url: The URL to fetch content from.

        Returns:
            A dictionary containing url, title, content, and diff information.
            Returns None if fetch fails.
        """
        return await self._content_service.fetch_content(url)

    async def fetch_full_content(self, url: str) -> Optional[str]:
        """
        Fetches the full content of a URL and converts it to markdown.

        Args:
            url: The URL of the content to fetch.

        Returns:
            Markdown content if successful, None otherwise.
        """
        return await self._content_service.fetch_full_content(url)

    async def analyze_content(
        self,
        content_results: Union[Dict, List[Dict]],
        prompt_template: str,
        batch_size: int = 3500,
    ) -> Dict[str, List[Dict]]:
        """
        Analyzes content from one or multiple URLs, optimizing
        API calls through batching.

        Args:
            content_results: Single content result or list of content results
              from fetch_content.
            prompt_template: Template for the analysis prompt.
            batch_size: Maximum size of each batch in tokens.

        Returns:
            Dictionary mapping URLs to their analyzed items.
        """
        return await self._content_service.analyze_content(
            content_results=content_results,
            prompt_template=prompt_template,
            batch_size=batch_size,
        )


# Factory function to create adapter from existing ContentService
def create_content_adapter(
    jina_api_key: str,
    openai_api_key: str,
    categories: List[str],
    markdown_storage,
    item_storage,
    token_tracker,
    min_threshold: float,
    max_threshold: float,
    content_service: ContentService = None,
) -> IContentService:
    """
    Factory function to create ContentServiceAdapter.

    Args:
        jina_api_key: Jina AI API key
        openai_api_key: OpenAI API key
        categories: List of categories
        markdown_storage: Markdown storage instance
        item_storage: Item storage instance
        token_tracker: Token tracker instance
        min_threshold: Minimum threshold for content filtering
        max_threshold: Maximum threshold for content filtering
        content_service: Existing ContentService instance, creates new one if None

    Returns:
        IContentService implementation (ContentServiceAdapter)
    """
    if content_service is None:
        content_service = ContentService(
            jina_api_key=jina_api_key,
            openai_api_key=openai_api_key,
            categories=categories,
            markdown_storage=markdown_storage,
            item_storage=item_storage,
            token_tracker=token_tracker,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
        )

    return ContentServiceAdapter(content_service)
