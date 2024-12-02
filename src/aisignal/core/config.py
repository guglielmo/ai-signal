from pathlib import Path
from typing import List

import yaml

from .config_schema import AppConfiguration


class ConfigManager:
    """
    Manages application configuration by loading from and saving to a YAML file,
    specifically managing paths and API keys.
    """

    def __init__(self, config_path: Path = None):
        self.config_path = (
            config_path or Path.home() / ".config" / "aisignal" / "config.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> AppConfiguration:
        """
        Loads the application configuration from the specified configuration path.

        :return: An instance of AppConfiguration loaded with settings from the
         configuration path.
        :rtype: AppConfiguration
        """
        return AppConfiguration.load(self.config_path)

    @property
    def categories(self) -> List[str]:
        """Gets the list of categories from the configuration.

        :return: A list of category names as strings.
        """
        return self.config.categories

    @property
    def sources(self) -> List[str]:
        """
        Retrieves the list of source strings from the configuration.

        :return: A list containing the source strings as specified in the
         configuration.
        """
        return self.config.sources

    @property
    def content_extraction_prompt(self) -> str:
        """Retrieves the content extraction prompt from the configuration.

        :return: The content extraction prompt as a string.
        """
        return self.config.prompts.content_extraction

    @property
    def obsidian_vault_path(self) -> str:
        """
        Retrieves the path to the Obsidian vault as specified in the configuration.

        :return: The file path to the Obsidian vault as a string.
        """
        return self.config.obsidian.vault_path

    @property
    def obsidian_template_path(self) -> str:
        """
        Retrieves the file path for the Obsidian template.

        :return: The Obsidian template path as a string.
        """
        return self.config.obsidian.template_path

    @property
    def openai_api_key(self) -> str:
        """
        Retrieves the OpenAI API key from the configuration.

        :return: The OpenAI API key as a string.
        """
        return self.config.api_keys.openai

    @property
    def jina_api_key(self) -> str:
        """
        Retrieves the Jina API key from the configuration.

        :return: Jina API key as a string.
        """
        return self.config.api_keys.jinaai

    @property
    def min_threshold(self) -> float:
        """
        Returns the minimum threshold value set in the current configuration.

        :return: The minimum threshold as a float.
        """
        return self.config.min_threshold

    @property
    def max_threshold(self) -> float:
        """Gets the maximum threshold value from the current configuration.

        :return: The maximum threshold value as a float.
        """
        return self.config.max_threshold

    def save(self, new_config: dict) -> None:
        """
        Saves a new configuration by merging it with the existing configuration to
        preserve any unmodified settings. It updates the relevant parts of the config
        and writes it back to the designated path in YAML format.

        :param new_config: The new configuration values to be merged with the
         existing configuration.
        :type new_config: dict
        :returns: None
        """
        # Merge with existing config to preserve any unmodified settings

        updated_config = {
            "api_keys": new_config["api_keys"],
            "categories": new_config["categories"],
            "sources": new_config["sources"],
            "obsidian": new_config["obsidian"],
            "sync_interval": new_config["sync_interval"],
            "max_threshold": new_config["max_threshold"],
            "min_threshold": new_config["min_threshold"],
            "prompts": self.config.prompts.to_dict(),  # Preserve existing prompts
        }

        # Create parent directories if they don't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.config_path, "w") as f:
            yaml.safe_dump(updated_config, f)
