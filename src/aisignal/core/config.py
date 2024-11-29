from pathlib import Path
from typing import List

import yaml

from .config_schema import AppConfiguration


class ConfigManager:
    def __init__(self, config_path: Path = None):
        self.config_path = (
            config_path or Path.home() / ".config" / "aisignal" / "config.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> AppConfiguration:
        return AppConfiguration.load(self.config_path)

    @property
    def categories(self) -> List[str]:
        return self.config.categories

    @property
    def sources(self) -> List[str]:
        return self.config.sources

    @property
    def content_extraction_prompt(self) -> str:
        return self.config.prompts.content_extraction

    @property
    def obsidian_vault_path(self) -> str:
        return self.config.obsidian.vault_path

    @property
    def obsidian_template_path(self) -> str:
        return self.config.obsidian.template_path

    @property
    def openai_api_key(self) -> str:
        return self.config.api_keys.openai

    @property
    def jina_api_key(self) -> str:
        return self.config.api_keys.jinaai

    def save(self, new_config: dict) -> None:
        """Save updated configuration"""
        # Merge with existing config to preserve any unmodified settings

        updated_config = {
            "api_keys": new_config["api_keys"],
            "categories": new_config["categories"],
            "sources": new_config["sources"],
            "obsidian": new_config["obsidian"],
            "prompts": self.config.prompts.to_dict(),  # Preserve existing prompts
        }

        # Create parent directories if they don't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.config_path, "w") as f:
            yaml.safe_dump(updated_config, f)
