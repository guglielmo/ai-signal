import re
from typing import Dict, List, Optional

import aiohttp
import openai
from textual import log

from aisignal.services.storage import MarkdownSourceStorage, ParsedItemStorage


class ContentService:
    """
    ContentService class provides methods for fetching content from a URL using
    Jina AI Reader and analyzing it with OpenAI.

    __init__(self, jina_api_key: str, openai_api_key: str, categories: List[str]):
        Initialize ContentService with Jina API key, OpenAI API key,
        and a list of categories.

    fetch_content(self, url: str) -> Optional[Dict]:
        Fetch content from URL using Jina AI Reader.

    _extract_title(markdown: str) -> str:
        Extract title from markdown content.

    analyze_content(self, content: str, prompt_template: str) -> List[Dict]:
        Analyze content using OpenAI API.

    _parse_markdown_items(self, markdown_text: str) -> List[Dict]:
        Parse markdown formatted items into structured data.
    """

    def __init__(
        self,
        jina_api_key: str,
        openai_api_key: str,
        categories: List[str],
        markdown_storage: MarkdownSourceStorage,
        item_storage: ParsedItemStorage,
    ):
        self.jina_api_key = jina_api_key
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.categories = categories
        self.markdown_storage = markdown_storage
        self.item_storage = item_storage

    async def fetch_content(self, url: str) -> Optional[Dict]:
        """
        Fetch content from URL and compare with stored version.

        :param url: The URL to fetch content from.
        :return: A dictionary containing:
            - url: Original URL
            - title: Extracted title
            - content: Full markdown content
            - diff: ContentDiff object with changes if any
            Returns None if fetch fails.
        """
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {
                "Authorization": f"Bearer {self.jina_api_key}",
                "X-No-Gfm": "true",
                "X-Retain-Images": "none",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status != 200:
                        log.error(f"Jina AI error: {response.status} {response.reason}")
                        return None

                    new_content = await response.text()
                    title = self._extract_title(new_content)
                    # Get diff from storage
                    content_diff = self.markdown_storage.get_content_diff(
                        url, new_content
                    )
                    # Store new content if there are changes

                    if content_diff.has_changes:
                        self.markdown_storage.store_content(url, new_content)

                    return {
                        "url": url,
                        "title": title,
                        "content": new_content,
                        "diff": content_diff,
                    }
        except Exception:
            return None

    async def analyze_content(
        self, content_result: Dict, prompt_template: str
    ) -> List[Dict]:
        """
        Analyze content changes using OpenAI.

        :param content_result: Dictionary from fetch_content containing content and diff
        :param prompt_template: The template of the prompt to be used for
          generating the analysis.
        :return: A list of dictionaries containing the parsed analysis results
          from the response.
        """
        log.info(f"Analyzing {content_result['url']}")

        if not content_result["diff"].has_changes:
            log.info(
                f"No changes detected for {content_result['url']}, using stored items"
            )
            return self.item_storage.get_stored_items(content_result["url"])

        # If there are new blocks, analyze only those
        if content_result["diff"].added_blocks:
            content_to_analyze = "\n\n".join(content_result["diff"].added_blocks)
            log.info(f"Analyzing {len(content_result['diff'].added_blocks)} new blocks")
        else:
            content_to_analyze = content_result["content"]
            log.info("No specific blocks identified, analyzing full content")

        categories_list = "\n".join(f"  - {cat}" for cat in self.categories)
        full_prompt = (
            f"{prompt_template}\n\n"
            f"Available categories:\n{categories_list}\n\n"
            f"Content to analyze:\n{content_to_analyze}"
        )

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
        )
        log.info(f"Total tokens used: {response.usage.total_tokens}")
        parsed_items = self._parse_markdown_items(response.choices[0].message.content)

        # Filter out already stored items
        new_items = self.item_storage.filter_new_items(
            content_result["url"], parsed_items
        )

        if new_items:
            # Store new items
            self.item_storage.store_items(content_result["url"], new_items)
            log.info(f"Stored {len(new_items)} new items")

            # Return all items for this source
            return self.item_storage.get_stored_items(content_result["url"])
        else:
            log.info("No new items to store")
            return []

    @staticmethod
    def _extract_title(markdown: str) -> str:
        """
        :param markdown: A string representing the markdown content from which
          to extract the title.
        :return: The extracted title as a string if found, otherwise
          "No title found".
        """
        for line in markdown.split("\n"):
            if line.startswith("Title:") or line.startswith("#"):
                return line.replace("Title:", "").replace("#", "").strip()
        return "No title found"

    def _parse_markdown_items(self, markdown_text: str) -> List[Dict]:
        """
        :param markdown_text: A string containing the markdown text to be parsed.
        :return: A list of dictionaries, each representing a parsed markdown
          item with keys like title, source, link, and categories.
        """
        items = []
        current_item = None

        for line in markdown_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if re.match(r"^\d+\.", line):
                if current_item:
                    items.append(current_item)
                current_item = {
                    "title": "",
                    "source": "",
                    "link": "",
                    "categories": [],
                    "summary": "",
                    "full_content": "",
                }
                title_match = re.search(r"^\d+\.\s*\*\*Title:\*\* (.*)", line)
                if title_match:
                    current_item["title"] = title_match.group(1)

            elif current_item:
                if line.startswith("**Source:**"):
                    current_item["source"] = line.replace("**Source:**", "").strip()
                elif line.startswith("**Link:**"):
                    current_item["link"] = line.replace("**Link:**", "").strip()
                elif line.startswith("**Categories:**"):
                    cats = line.replace("**Categories:**", "").strip()
                    current_item["categories"] = [
                        cat.strip()
                        for cat in cats.split(",")
                        if cat.strip() in self.categories
                    ]
                elif line.startswith("**Summary:**"):
                    current_item["summary"] = line.replace("**Summary:**", "").strip()

        if current_item:
            items.append(current_item)

        return [item for item in items if item["title"] and item["link"]]
