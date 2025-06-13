"""
Config Manager Adapter for AI Signal Core.

This adapter wraps the existing ConfigManager to implement IConfigManager
interface without modifying the original implementation.
"""

from typing import List

from aisignal.core.config import ConfigManager
from aisignal.core.interfaces import IConfigManager


class ConfigManagerAdapter(IConfigManager):
    """
    Adapter that wraps the existing ConfigManager to implement IConfigManager.

    This follows the Adapter pattern to make existing ConfigManager work
    with the new Core architecture without modifying the original class.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize adapter with existing ConfigManager instance.

        Args:
            config_manager: Existing ConfigManager instance to wrap
        """
        self._config_manager = config_manager

    @property
    def categories(self) -> List[str]:
        """Gets the list of categories from the configuration."""
        return self._config_manager.categories

    @property
    def sources(self) -> List[str]:
        """Retrieves the list of source strings from the configuration."""
        return self._config_manager.sources

    @property
    def content_extraction_prompt(self) -> str:
        """Retrieves the content extraction prompt from the configuration."""
        return self._config_manager.content_extraction_prompt

    @property
    def obsidian_vault_path(self) -> str:
        """Retrieves the path to the Obsidian vault
        as specified in the configuration."""
        return self._config_manager.obsidian_vault_path

    @property
    def obsidian_template_path(self) -> str:
        """Retrieves the file path for the Obsidian template."""
        return self._config_manager.obsidian_template_path

    @property
    def openai_api_key(self) -> str:
        """Retrieves the OpenAI API key from the configuration."""
        return self._config_manager.openai_api_key

    @property
    def jina_api_key(self) -> str:
        """Retrieves the Jina API key from the configuration."""
        return self._config_manager.jina_api_key

    @property
    def min_threshold(self) -> float:
        """Returns the minimum threshold value set in the current configuration."""
        return self._config_manager.min_threshold

    @property
    def max_threshold(self) -> float:
        """Gets the maximum threshold value from the current configuration."""
        return self._config_manager.max_threshold

    @property
    def sync_interval(self) -> int:
        """Gets the sync interval value from the current configuration."""
        return self._config_manager.sync_interval

    def save(self, new_config: dict) -> None:
        """
        Saves a new configuration by merging it with the existing configuration.

        Args:
            new_config: The new configuration values to be merged
            with the existing configuration.
        """
        self._config_manager.save(new_config)


# Factory function to create adapter from existing ConfigManager
def create_config_adapter(config_manager: ConfigManager = None) -> IConfigManager:
    """
    Factory function to create ConfigManagerAdapter.

    Args:
        config_manager: Existing ConfigManager instance, creates new one if None

    Returns:
        IConfigManager implementation (ConfigManagerAdapter)
    """
    if config_manager is None:
        config_manager = ConfigManager()

    return ConfigManagerAdapter(config_manager)
