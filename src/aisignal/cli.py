import os
from pathlib import Path
from typing import Optional

import toml
import typer
import yaml
from rich.console import Console

from aisignal.core.config_schema import AppConfiguration

from .app import ContentCuratorApp

console = Console()
app = typer.Typer(
    name="aisignal",
    help="Terminal-based AI curator that "
    "turns information noise into meaningful signal",
    add_completion=False,
)

CONFIG_DIR = Path.home() / ".config" / "aisignal"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def ensure_config():
    """
    Ensures that the configuration directory and file exist. If the configuration
    file does not exist, it creates the file with default settings.

    This method performs the following actions:
    - Creates the configuration directory if it doesn't exist.
    - Checks for the existence of the configuration file.
    - Writes the default configuration settings to the file if it doesn't exist.

    :return: None
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        default_config = AppConfiguration.get_default_config()
        CONFIG_FILE.write_text(yaml.dump(default_config, sort_keys=False))


def get_version() -> str:
    """
    Retrieve the version of the project from the 'pyproject.toml' file.

    The method reads the 'pyproject.toml' file located in the parent of the
    parent directory of the current file and extracts the project version
    specified under the 'tool.poetry.version' key.

    :return: The version string of the project.
    :rtype: str
    """
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
    """
    Initializes the configuration file for the application. This command will write
    a configuration file if it does not already exist or overwrite the existing one
    if the force option is used.

    :param force: A boolean option to force initialization even when a configuration
      file already exists. If set to True, the config file will be overwritten.
    :raises Exit: Exits the application if the config file already exists and force
      is not specified.
    """
    if CONFIG_FILE.exists() and not force:
        console.print(
            "[yellow]Config file already exists. Use --force to overwrite.[/]"
        )
        raise typer.Exit()

    ensure_config()
    console.print("[green]Configuration initialized at:[/] " + str(CONFIG_FILE))
    console.print("\nYou can now edit the configuration file and run [bold]aisignal[/]")


@app.command()
def config():
    """
    Opens the configuration file in the user's preferred text editor. If the EDITOR
    environment variable is not set, defaults to using 'vim'.

    :return: None
    """
    ensure_config()
    editor = os.environ.get("EDITOR", "vim")
    os.system(f"{editor} {CONFIG_FILE}")


@app.command()
def validate():
    """
    Validates the configuration file by checking for the existence of required fields.
    If the configuration file does not exist, prompts the user to initialize it first.
    Checks for certain required fields in the configuration file and reports missing
    fields. If validation is successful, the function will print a success message.
    In case of an error, it displays the error message and exits the application.

    Raises:
      typer.Exit: If the configuration file does not exist or if there is an error
      during validation.
      ValueError: If any required field is missing from the configuration file.
    """
    if not CONFIG_FILE.exists():
        console.print("[red]Config file not found. Run 'aisignal init' first.[/]")
        raise typer.Exit(1)

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        # Add validation logic here
        required_fields = [
            "sources",
            "prompts",
            "categories",
            "quality_threshold",
            "sync_interval",
            "api_keys",
            "obsidian",
            "social",
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
    """
    Synchronizes the content by executing the sync action of the ContentCuratorApp.

    Checks for the existence of the configuration file. If the file does not
    exist, prints an error message and exits the application. If the file
    exists, initializes the ContentCuratorApp and performs the sync action.
    Prints a completion message when finished.

    :raises typer.Exit: If the configuration file is not found.
    """
    if not CONFIG_FILE.exists():
        console.print("[red]Config file not found. Run 'aisignal init' first.[/]")
        raise typer.Exit(1)

    app = ContentCuratorApp()
    app.action_sync()
    console.print("[green]Sync completed![/]")


@app.command()
def version():
    """
    Displays the current version of the AI Signal application.

    This function retrieves the application version using the `get_version()`
    function and prints it to the console in the format "AI Signal version: <ver>".

    :return: None
    """
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
    """
    Runs the Content Curator application with the specified configuration options.
    If a configuration file path is provided, it checks for its existence and runs
    the application using that configuration. If the file does not exist, it
    prints an error message and exits with a status code of 1. If no configuration
    file path is provided, it uses default settings.

    :param config_path: Optional; a Path object representing the location of a
      custom configuration file. Specified via command-line options '--config' or
      '-c'.
    :return: None
    """
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
