import ast
import re
from typing import Dict, List, Optional, Union

import aiohttp
import openai
from textual import log

from aisignal.core.token_tracker import COST_PER_MILLION, TokenTracker
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
        token_tracker: TokenTracker,
        min_threshold: float,  # New parameter
        max_threshold: float,  # New parameter
    ):
        """
        Initializes the class with the necessary API keys, category list,
         storage options, token tracker, and threshold values.

        :param jina_api_key:
          The API key required to access Jina services.
        :param openai_api_key:
          The API key needed to connect to OpenAI services for API operations.
        :param categories:
          A list of categories used for classifying or organizing data.
        :param markdown_storage:
          An instance of MarkdownSourceStorage for handling markdown data.
        :param item_storage:
          An instance of ParsedItemStorage for managing parsed items.
        :param token_tracker:
          A TokenTracker instance used to track or manage API token usage.
        :param min_threshold:
          The minimum threshold value for a specific operation or configuration.
        :param max_threshold:
          The maximum threshold value for a specific operation or configuration.
        """
        self.jina_api_key = jina_api_key
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.categories = categories
        self.markdown_storage = markdown_storage
        self.item_storage = item_storage
        self.token_tracker = token_tracker
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    async def _get_jina_wallet_balance(self) -> Optional[float]:
        """
        Fetches the current Jina AI wallet balance.

        :return: Current token balance if successful, None if request fails
        """
        try:
            url = (
                f"https://embeddings-dashboard-api.jina.ai/api/v1/api_key/user"
                f"?api_key={self.jina_api_key}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        log.error(
                            f"Failed to fetch Jina wallet balance: {response.status}"
                        )
                        return None

                    data = await response.json()
                    return data.get("wallet", {}).get("total_balance")

        except Exception as e:
            log.error(f"Error fetching Jina wallet balance: {e}")
            return None

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
                    estimated_tokens = self.token_tracker.estimate_jina_tokens(
                        new_content
                    )
                    self.token_tracker.add_jina_usage(new_content)
                    log.info(
                        f"JinaAI tokens for {url}: "
                        f"{estimated_tokens:,} tokens "
                        f"(${(estimated_tokens * 0.02 / 1_000_000):.6f})"
                    )

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
        except Exception as e:
            log.error(f"Fetch error: {e}")
            return None

    # In content.py, add to ContentService class

    async def fetch_full_content(self, url: str) -> Optional[str]:
        """
        Fetches the full content of a URL and converts it to markdown using Jina AI.

        :param url: The URL of the content to fetch
        :return: Markdown content if successful, None otherwise
        """
        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {
                "Authorization": f"Bearer {self.jina_api_key}",
                "X-No-Gfm": "true",  # No GitHub-flavored markdown
                "X-Retain-Images": "none",  # Don't include images
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status != 200:
                        log.error(
                            "Jina AI error fetching full content: "
                            f"{response.status} {response.reason}"
                        )
                        return None

                    content = await response.text()

                    # Track token usage for this additional API call
                    estimated_tokens = self.token_tracker.estimate_jina_tokens(content)
                    self.token_tracker.add_jina_usage(content)
                    estimated_cost = (
                        estimated_tokens * COST_PER_MILLION["jina"] / 1_000_000
                    )
                    log.info(
                        f"JinaAI tokens for full content of {url}: "
                        f"{estimated_tokens:,} tokens "
                        f"(${estimated_cost:.6f})"
                    )

                    return content

        except Exception as e:
            log.error(f"Error fetching full content from {url}: {e}")
            return None

    async def analyze_content(
        self,
        content_results: Union[Dict, List[Dict]],
        prompt_template: str,
        batch_size: int = 3500,
    ) -> Dict[str, List[Dict]]:
        """
        Analyzes content from one or multiple URLs,
        optimizing API calls through batching.

        Args:
            content_results: Single content result or
                list of content results from fetch_content
            prompt_template: Template for the analysis prompt
            batch_size: Maximum size of each batch in tokens (default: 3500)

        Returns:
            Dictionary mapping URLs to their analyzed items
        """
        # Handle single content result
        if isinstance(content_results, dict):
            content_results = [content_results]

        # Step 1: Initialize results and group contents needing analysis
        results = {}
        contents_to_analyze = {}

        for content_result in content_results:
            url = content_result["url"]

            # Step 1a: Skip unchanged content
            if not content_result["diff"].has_changes:
                log.info(f"No changes detected for {url}")
                continue

            # Step 1b: Get content blocks to analyze
            if not content_result["diff"].added_blocks:
                log.warning(f"Diff indicates changes but no added blocks for {url}")
                continue
            content_to_analyze = "\n\n".join(content_result["diff"].added_blocks)
            log.info(
                f"Analyzing {len(content_result['diff'].added_blocks)} "
                f"new blocks for {url}"
            )
            log.debug(f"New blocks: {content_result['diff'].added_blocks}")

            contents_to_analyze[url] = content_to_analyze

        # Step 2: Prepare batches for analysis
        batches = []
        current_batch = []
        current_batch_size = 0

        for url, content in contents_to_analyze.items():
            content_section = f"## {url}\n\n{content}\n\n"
            estimated_tokens = len(content_section) // 4  # rough estimation

            if current_batch_size + estimated_tokens > batch_size and current_batch:
                batches.append("\n".join(current_batch))
                current_batch = [content_section]
                current_batch_size = estimated_tokens
            else:
                current_batch.append(content_section)
                current_batch_size += estimated_tokens

        if current_batch:
            batches.append("\n".join(current_batch))

        # Step 3: Process each batch
        categories_list = "\n".join(f"  - {cat}" for cat in self.categories)

        for batch_content in batches:
            batch_results = await self._process_batch_content(
                batch_content, prompt_template, categories_list
            )
            results.update(batch_results)

        return results

    async def _process_batch_content(
        self, batch_content: str, prompt_template: str, categories_list: str
    ) -> Dict[str, List[Dict]]:
        """
        Process a single batch of content through the AI and handle the results.

        Args:
            batch_content: Content from multiple URLs formatted with headers
            prompt_template: Template for the AI prompt
            categories_list: Formatted list of available categories

        Returns:
            Dictionary mapping URLs to their analyzed and processed items
        """
        # Step 1: Get AI analysis
        ai_response = await self._get_ai_analysis(
            batch_content, prompt_template, categories_list
        )

        # Step 2: Process AI response for each URL
        return await self._process_urls_items(ai_response)

    async def _get_ai_analysis(
        self, content: str, prompt_template: str, categories_list: str
    ) -> str:
        """
        Send content to AI for analysis and handle token tracking.
        """
        # Prepare prompt
        full_prompt = (
            f"{prompt_template}\n\n"
            f"Categories\n==========\n{categories_list}\n\n"
            f"Content\n=======\n{content}\n"
        )
        log.debug(f"PROMPT\n\n{full_prompt}\n")

        # Get AI response
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
        )

        # Track token usage
        self._track_token_usage(response.usage)

        returned_content = response.choices[0].message.content
        log.debug(f"Content returned from AI: {returned_content}")
        return returned_content

    def _track_token_usage(self, usage):
        """Track and log token usage and costs."""
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        prompt_cost = prompt_tokens * 0.15 / 1_000_000
        completion_cost = completion_tokens * 0.60 / 1_000_000
        total_cost = prompt_cost + completion_cost

        log.info(
            f"OpenAI tokens for batch:\n"
            f"  Input:  {prompt_tokens:,} tokens (${prompt_cost:.6f})\n"
            f"  Output: {completion_tokens:,} tokens (${completion_cost:.6f})\n"
            f"  Total:  {total_tokens:,} tokens (${total_cost:.6f})"
        )

        self.token_tracker.add_openai_usage(prompt_tokens, completion_tokens)

    async def _process_urls_items(self, content: str) -> Dict[str, List[Dict]]:
        """
        Process and store items for many URLs
        """
        # Parse items from content
        parsed_items = self._parse_markdown_items(content)

        # Group items by source URL
        items_by_url = {}
        for item in parsed_items:
            source_url = item["source"]
            if source_url not in items_by_url:
                items_by_url[source_url] = []

            # Filter and enhance quality items
            if item["ranking"] >= self.min_threshold:
                if item["ranking"] >= self.max_threshold:
                    full_content = await self.fetch_full_content(item["link"])
                    if full_content:
                        item["full_content"] = full_content
                items_by_url[source_url].append(item)
            else:
                log.info(
                    f"Discarding item {item['title']} "
                    f"with ranking {item['ranking']}"
                )

        # Process each URL's items
        results = {}
        for source_url, items in items_by_url.items():
            # Handle new items
            new_items = self.item_storage.filter_new_items(source_url, items)

            if new_items:
                self.item_storage.store_items(source_url, new_items)
                log.info(f"Stored {len(new_items)} new items for {source_url}")
                results[source_url] = self.item_storage.get_stored_items(source_url)
            else:
                log.info(f"No new items to store for {source_url}")
                results[source_url] = []

        return results

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
                elif line.startswith("**Rankings:**"):
                    values = ast.literal_eval(line.replace("**Rankings:**", "").strip())
                    if len(values) != 3:
                        log.warning(
                            f"Invalid rankings for {current_item['title']}: {values}"
                        )
                        continue
                    v1, v2, v3 = values
                    w_avg = v1 * 30 + v2 * 50 + v3 * 20
                    current_item["ranking"] = round(w_avg)

        if current_item:
            items.append(current_item)

        return [item for item in items if item["title"] and item["link"]]
