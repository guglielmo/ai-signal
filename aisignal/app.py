import re

import html2text
from bs4 import BeautifulSoup
from readability import Document
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Button, Static, DataTable,
    Input, Switch, ProgressBar, Label, ListView, ListItem
)
from textual.binding import Binding
from datetime import datetime
import webbrowser
import yaml
import asyncio
import aiohttp

from pathlib import Path
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from rich.markdown import Markdown
import openai


@dataclass
class Resource:
    """Data class for content resources"""
    id: str
    title: str
    url: str
    categories: List[str]
    ranking: float
    summary: str
    content: str
    datetime: datetime
    source: str


class ResourceFilterState:
    """State management for resource filtering"""

    def __init__(self):
        self.selected_categories: List[str] = []
        self.selected_sources: List[str] = []
        self.sort_by_datetime: bool = False


class ResourceDetailScreen(Screen):
    """Screen for displaying resource details"""
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        ("o", "open_browser", "Open in Browser"),
        ("s", "share", "Share"),
        ("e", "export", "Export to Obsidian"),
    ]

    def __init__(self, resource: Resource):
        super().__init__()
        self.resource = resource

    def compose(self) -> ComposeResult:
        yield Container(
            Static(Markdown(self.resource.content), id="content"),
            Button("Open in Browser", id="open_browser"),
            Button("Share", id="share"),
            Button("Export to Obsidian", id="export"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open_browser":
            webbrowser.open(self.resource.url)
        elif event.button.id == "share":
            self.app.push_screen(ShareScreen(self.resource))
        elif event.button.id == "export":
            self.app.export_to_obsidian(self.resource)


class ShareScreen(Screen):
    """Screen for sharing options"""

    def __init__(self, resource: Resource):
        super().__init__()
        self.resource = resource

    def compose(self) -> ComposeResult:
        yield Container(
            Button("Share on Twitter", id="twitter"),
            Button("Share on LinkedIn", id="linkedin"),
        )


class ContentCuratorApp(App):
    """Main application class"""
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "toggle_config", "Config", show=True),
        Binding("s", "sync", "Sync", show=True),
        Binding("f", "toggle_filters", "Filters", show=True),
    ]

    def __init__(self, config_path: Optional[Path] = None):
        super().__init__()
        self.config_path = config_path or Path.home() / ".config" / "aisignal" / "config.yaml"
        self.config = self._load_config()
        self.resources: List[Resource] = []
        self.filter_state = ResourceFilterState()
        self.is_syncing = False

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        with Container():
            with Horizontal():
                # Left sidebar with filters
                with Container(id="sidebar"):
                    yield Label("Categories")
                    yield ListView(id="category_filter")
                    yield Label("Sources")
                    yield ListView(id="source_filter")

                    with Container(id="sync_status"):
                        yield ProgressBar(id="sync_progress", show_eta=False)

                # Main content area
                with Vertical(id="main_content"):
                    yield DataTable(id="resource_list")


        yield Footer()

    def on_mount(self) -> None:
        """Set up the application when mounted"""
        self.log("Application mounted")

        # Initialize resource list
        table = self.query_one("#resource_list", DataTable)
        table.add_columns("Title", "Source", "Categories", "Ranking", "Date")

        # Initialize filters
        self._setup_filters()

        # Start initial sync
        self.action_sync()

    def _setup_filters(self) -> None:
        """Setup category and source filters"""
        category_list = self.query_one("#category_filter", ListView)
        source_list = self.query_one("#source_filter", ListView)

        category_list.clear()
        source_list.clear()

        for category in self.config["categories"]:
            category_list.append(ListItem(Label(category)))

        for url in self.config["sources"]:
            source_list.append(ListItem(Label(url)))

    async def _fetch_content(self, url: str, jina_api_key: str) -> Optional[Dict]:
        """
        Fetch content from URL and convert to markdown using Jina AI Reader

        Args:
            url: The URL to fetch content from
            jina_api_key: Your Jina AI API key

        Returns:
            Dictionary containing url, title and markdown content, or None if failed
        """
        try:
            jina_url = f'https://r.jina.ai/{url}'
            headers = {
                'Authorization': f'Bearer {jina_api_key}',
                'X-No-Gfm': 'true',  # Disable GitHub Flavored Markdown
                'X-Retain-Images': 'none'  # Don't include images
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status != 200:
                        self.log(f"Jina AI API error: {response.status} - {await response.text()}")
                        return None

                    markdown_content = await response.text()

                    # Extract title from markdown - usually the first # heading
                    title = "No title found"
                    for line in markdown_content.split('\n'):
                        if line.startswith('# '):
                            title = line.replace('# ', '').strip()
                            break

                    return {
                        "url": url,
                        "title": title,
                        "content": markdown_content
                    }
        except Exception as e:
            self.log(f"Error fetching {url}: {str(e)}")
            return None

    def action_sync(self) -> None:
        """Start content synchronization"""
        self.log("Starting action_sync")
        if not self.is_syncing:
            asyncio.create_task(self._sync_content())

    async def _sync_content(self) -> None:
        """Synchronize content from all sources"""
        self.is_syncing = True
        progress = self.query_one("#sync_progress", ProgressBar)
        client = openai.AsyncOpenAI(api_key=self.config["api_keys"]["openai"])
        categories_list = "\n".join(f"  - {cat}" for cat in self.config["categories"])

        try:
            total_urls = len(self.config["sources"])
            progress.update(total=100)

            new_resources = []
            prompt_template = self.config["prompts"]["content_extraction"]

            for i, url in enumerate(self.config["sources"]):
                self.log("_sync_content:url", url)
                progress.advance((i+1)/total_urls * 100)

                content = await self._fetch_content(url, self.config["api_keys"]["jinaai"])
                if not content:
                    self.log("Could not fetch content from URL", url)
                    continue

                try:
                    full_prompt = (
                        f"{prompt_template}\n\n"
                        f"Available categories:\n{categories_list}\n\n"
                        f"Content to analyze:\n{content['content']}"
                    )

                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{
                            "role": "user",
                            "content": full_prompt,
                        }],
                        temperature=0.7
                    )
                    self.log("response", response.choices[0].message.content)
                    items = self._parse_markdown_items(response.choices[0].message.content)

                    for item in items:
                        resource = Resource(
                            id=str(len(new_resources)),
                            title=item['title'],
                            url=item['link'],
                            categories=item['categories'],
                            ranking=0.0,
                            summary="",
                            content=content['content'],
                            datetime=datetime.now(),
                            source=item['source']
                        )
                        new_resources.append(resource)

                except Exception as e:
                    self.log(f"Error processing with OpenAI: {str(e)}")
                    continue

                self.resources = new_resources
                self.update_resource_list()

            self.update_resource_list()
        finally:
            self.is_syncing = False
            progress.update(progress=0)

    def _parse_markdown_items(self, markdown_text: str) -> List[Dict]:
        """Parse markdown formatted items into structured data"""
        items = []
        current_item = None
        valid_categories = set(self.config.get("categories", []))

        for line in markdown_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # New item starts with number
            if re.match(r'^\d+\.', line):
                if current_item:
                    items.append(current_item)
                current_item = {
                    'title': '',
                    'source': '',
                    'link': '',
                    'categories': []
                }
                # Extract title
                title_match = re.search(r'^\d+\.\s*\*\*Title:\*\* (.*)', line)
                if title_match:
                    current_item['title'] = title_match.group(1)

            elif current_item and line.startswith('**Source:**'):
                self.log("line", line)
                current_item['source'] = line.replace('**Source:**', '').strip()
            elif current_item and line.startswith('**Link:**'):
                current_item['link'] = line.replace('**Link:**', '').strip()
            elif current_item and line.startswith('**Categories:**'):
                cats = line.replace('**Categories:**', '').strip()
                current_item['categories'] = [
                    cat.strip() for cat in cats.split(',')
                    if cat.strip() in valid_categories
                ]

        # Add the last item
        if current_item:
            items.append(current_item)

        return [item for item in items if item['title'] and item['link']]

    def update_resource_list(self) -> None:
        """Update the resource list with filtered and sorted items"""
        table = self.query_one("#resource_list", DataTable)
        table.clear()

        filtered_resources = self._apply_filters(self.resources)
        sorted_resources = self._sort_resources(filtered_resources)

        for resource in sorted_resources:
            table.add_row(
                resource.title,
                resource.source,
                ", ".join(resource.categories),
                f"{resource.ranking:.2f}",
                resource.datetime.strftime("%Y-%m-%d %H:%M")
            )

    def _apply_filters(self, resources: List[Resource]) -> List[Resource]:
        """Apply category and source filters"""
        filtered = resources

        if self.filter_state.selected_categories:
            filtered = [
                r for r in filtered
                if any(c in r.categories for c in self.filter_state.selected_categories)
            ]

        if self.filter_state.selected_sources:
            filtered = [
                r for r in filtered
                if r.source in self.filter_state.selected_sources
            ]

        return filtered

    def _sort_resources(self, resources: List[Resource]) -> List[Resource]:
        """Sort resources based on current sort settings"""
        if self.filter_state.sort_by_datetime:
            return sorted(resources, key=lambda r: r.datetime, reverse=True)

        return sorted(
            resources,
            key=lambda r: (r.datetime.date(), r.ranking),
            reverse=True
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle resource selection"""
        resource = self.resources[event.row_key]
        self.push_screen(ResourceDetailScreen(resource))

    def export_to_obsidian(self, resource: Resource) -> None:
        """Export resource to Obsidian vault"""
        if not self.config["obsidian"]["vault_path"]:
            self.notify("Obsidian vault path not configured")
            return

        try:
            vault_path = Path(self.config["obsidian"]["vault_path"])
            file_path = vault_path / f"{resource.title}.md"

            # Use template if available
            template_path = self.config["obsidian"].get("template_path")
            if template_path and Path(template_path).exists():
                with open(template_path) as f:
                    template = f.read()
            else:
                template = "# {title}\n\n{content}\n\nSource: {url}"

            content = template.format(
                title=resource.title,
                content=resource.content,
                url=resource.url
            )

            file_path.write_text(content)
            self.notify(f"Exported to Obsidian: {file_path.name}")

        except Exception as e:
            self.notify(f"Export failed: {str(e)}")


def run_app(config_path: Optional[Path] = None):
    """Run the application with optional config path"""
    app = ContentCuratorApp(config_path)
    app.run()


if __name__ == "__main__":
    run_app()