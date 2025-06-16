"""
Configuration Service Implementation

This module implements the configuration service that directly handles
configuration management without wrapping legacy classes.
"""

from pathlib import Path
from typing import List

import yaml

from aisignal.core.config_schema import AppConfiguration
from aisignal.core.interfaces import IConfigManager


class ConfigService(IConfigManager):
    """
    Configuration service that directly implements configuration management.

    This replaces the old ConfigManager with a cleaner service-based approach.
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize the configuration service.

        Args:
            config_path: Optional path to the configuration file.
                        If None, uses the default path.
        """
        self.config_path = (
            config_path or Path.home() / ".config" / "aisignal" / "config.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> AppConfiguration:
        """
        Loads the application configuration from the specified configuration path.

        Returns:
            An instance of AppConfiguration loaded with settings from the
            configuration path.
        """
        return AppConfiguration.load(self.config_path)

    @property
    def categories(self) -> List[str]:
        """Gets the list of categories from the configuration."""
        return self.config.categories

    @property
    def sources(self) -> List[str]:
        """Retrieves the list of source strings from the configuration."""
        return self.config.sources

    @property
    def content_extraction_prompt(self) -> str:
        """Retrieves the content extraction prompt from the configuration."""
        return self.config.prompts.content_extraction

    @property
    def obsidian_vault_path(self) -> str:
        """Retrieves the path to the Obsidian vault as specified in the config."""
        return self.config.obsidian.vault_path

    @property
    def obsidian_template_path(self) -> str:
        """Retrieves the file path for the Obsidian template."""
        return self.config.obsidian.template_path

    @property
    def openai_api_key(self) -> str:
        """Retrieves the OpenAI API key from the configuration."""
        return self.config.api_keys.openai

    @property
    def jina_api_key(self) -> str:
        """Retrieves the Jina API key from the configuration."""
        return self.config.api_keys.jinaai

    @property
    def min_threshold(self) -> float:
        """Returns the minimum threshold value set in the current configuration."""
        return self.config.min_threshold

    @property
    def max_threshold(self) -> float:
        """Gets the maximum threshold value from the current configuration."""
        return self.config.max_threshold

    @property
    def sync_interval(self) -> int:
        """Gets the sync interval value from the current configuration."""
        return self.config.sync_interval

    def save(self, new_config: dict) -> None:
        """
        Saves a new configuration by merging it with the existing configuration.

        Args:
            new_config: The new configuration values to be merged
                       with the existing configuration.
        """
        # Create updated configuration with all values from new_config
        updated_config = {
            "api_keys": new_config["api_keys"],
            "categories": new_config["categories"],
            "sources": new_config["sources"],
            "obsidian": new_config["obsidian"],
            "sync_interval": new_config["sync_interval"],
            "max_threshold": new_config["max_threshold"],
            "min_threshold": new_config["min_threshold"],
            "prompts": new_config.get("prompts", self.config.prompts.to_dict()),
        }

        # Create parent directories if they don't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.config_path, "w") as f:
            yaml.safe_dump(updated_config, f)

        # Reload configuration
        self.config = self._load_config()

    def reload(self) -> None:
        """
        Reload the configuration from disk.

        This is useful when the configuration file has been modified externally.
        """
        self.config = self._load_config()

    def get_config_path(self) -> Path:
        """
        Get the path to the configuration file.

        Returns:
            Path to the configuration file.
        """
        return self.config_path
