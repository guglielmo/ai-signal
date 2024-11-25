import typer
from pathlib import Path
from typing import Optional
import yaml
from rich.console import Console
import toml
import os
from .app import ContentCuratorApp

console = Console()
app = typer.Typer(
    name="aisignal",
    help="Terminal-based AI curator that turns information noise into meaningful signal",
    add_completion=False,
)

CONFIG_DIR = Path.home() / ".config" / "aisignal"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

default_config = {
    "sources": [
        "https://news.ycombinator.com",
        "https://medium.com/tag/artificial-intelligence",
    ],
    "prompts": [
        {"content_extraction": """
Please extract the top 10 news, articles, posts, whatever items compose this list.

For each items, find or generate:
* the title
* the source (URL of the list source)
* the original URL of the item, or _link_
* the categories, among the available ones, listed below.

Generate a list of items in markdown format, strictly following this syntax:

# Top 10 Items

1. **Title:** Announcing the 6.x Django Steering Council elections 🚀  
   **Source:** https://django-news.com  
   **Link:** https://cur.at/3TNDN81?m=web  
   **Categories:** Django

2. **Title:** Django Channels 4.2.0 Release Notes  
   **Source:** https://django-news.com
   **Link:** https://cur.at/R9ZJhRV?m=web  
   **Categories:** Django
...

In particular, the Source should only contain the URL.        
        """}
    ],
    "categories": [
        "AI/ML",
        "Programming",
        "Security",
        "DevOps",
    ],
    "quality_threshold": 0.7,
    "sync_interval": 24,
    "obsidian": {
        "vault_path": "",
        "template_path": "",
    },
    "social": {
        "bluesky_template": "{title}\n\n{url}\n\n#AI #Content",
    },
    "api_keys": {
        "jinaai": "CHANGE ME",
        "openai": "CHANGE ME"
    }
}


def ensure_config():
    """Ensure config directory and file exist"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(yaml.dump(default_config, sort_keys=False))

def get_version() -> str:
    """Get version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject = toml.load(pyproject_path)
    return pyproject["tool"]["poetry"]["version"]


@app.command()
def init(
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Force initialization even if config exists",
        )
):
    """Initialize AI Signal configuration"""
    if CONFIG_FILE.exists() and not force:
        console.print("[yellow]Config file already exists. Use --force to overwrite.[/]")
        raise typer.Exit()

    ensure_config()
    console.print("[green]Configuration initialized at:[/] " + str(CONFIG_FILE))
    console.print("\nYou can now edit the configuration file and run [bold]aisignal[/]")


@app.command()
def config():
    """Edit configuration in your default editor"""
    ensure_config()
    editor = os.environ.get("EDITOR", "vim")
    os.system(f"{editor} {CONFIG_FILE}")


@app.command()
def validate():
    """Validate configuration file"""
    if not CONFIG_FILE.exists():
        console.print("[red]Config file not found. Run 'aisignal init' first.[/]")
        raise typer.Exit(1)

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        # Add validation logic here
        required_fields = [
            "sources", "prompts", "categories", "quality_threshold", "sync_interval", "api_keys", "obsidian", "social"
        ]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        console.print("[green]Configuration is valid![/]")
    except Exception as e:
        console.print(f"[red]Configuration error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def sync():
    """Force sync content from configured sources"""
    if not CONFIG_FILE.exists():
        console.print("[red]Config file not found. Run 'aisignal init' first.[/]")
        raise typer.Exit(1)

    app = ContentCuratorApp()
    app.action_sync()
    console.print("[green]Sync completed![/]")


@app.command()
def version():
    """Show version information"""
    ver = get_version()
    console.print(f"AI Signal version: {ver}")


@app.command()
def run(
        config_path: Optional[Path] = typer.Option(
            None,
            "--config",
            "-c",
            help="Path to custom config file",
        )
):
    """Launch the AI Signal TUI application"""
    if config_path:
        if not config_path.exists():
            console.print(f"[red]Config file not found: {config_path}[/]")
            raise typer.Exit(1)
    else:
        ensure_config()

    app = ContentCuratorApp()
    app.run()


def main():
    app()


if __name__ == "__main__":
    main()