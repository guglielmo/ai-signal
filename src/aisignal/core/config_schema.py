from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import yaml
from yaml.parser import ParserError


class ConfigError(Exception):
    """Base class for configuration errors"""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails"""
    pass


class ConfigFileError(ConfigError):
    """Raised when there are issues with the configuration file"""
    pass


@dataclass
class APIKeys:
    jinaai: str
    openai: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'APIKeys':
        required_keys = {'jinaai', 'openai'}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ConfigValidationError(f"Missing required API keys: {missing_keys}")
        return cls(**{k: data[k] for k in required_keys})


@dataclass
class ObsidianConfig:
    vault_path: str
    template_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'ObsidianConfig':
        if 'vault_path' not in data:
            raise ConfigValidationError("Obsidian configuration missing vault_path")
        return cls(**data)


@dataclass
class Prompts:
    content_extraction: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'Prompts':
        if 'content_extraction' not in data:
            raise ConfigValidationError("Missing content_extraction prompt")
        return cls(**data)


@dataclass
class AppConfiguration:
    categories: List[str]
    sources: List[str]
    api_keys: APIKeys
    prompts: Prompts
    obsidian: ObsidianConfig

    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfiguration':
        try:
            return cls(
                categories=data['categories'],
                sources=data['sources'],
                api_keys=APIKeys.from_dict(data['api_keys']),
                prompts=Prompts.from_dict(data['prompts']),
                obsidian=ObsidianConfig.from_dict(data['obsidian'])
            )
        except KeyError as e:
            raise ConfigValidationError(f"Missing required configuration key: {e}")

    @classmethod
    def load(cls, config_path: Path) -> 'AppConfiguration':
        """Load and validate configuration from file"""
        try:
            if not config_path.exists():
                raise ConfigFileError(f"Configuration file not found: {config_path}")

            with open(config_path) as f:
                try:
                    data = yaml.safe_load(f)
                except ParserError as e:
                    raise ConfigFileError(f"Invalid YAML in configuration file: {e}")

            return cls.from_dict(data)

        except (ConfigError, yaml.YAMLError) as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    @staticmethod
    def get_default_config() -> Dict:
        """Return default configuration structure"""
        return {
            "categories": [
                "AI",
                "Programming",
                "Data Science",
                "Machine Learning"
            ],
            "sources": [
                "https://example.com/blog1",
                "https://example.com/blog2"
            ],
            "api_keys": {
                "jinaai": "your-jina-api-key",
                "openai": "your-openai-api-key"
            },
            "prompts": {
                "content_extraction": "Default prompt for content extraction"
            },
            "obsidian": {
                "vault_path": "/path/to/your/vault",
                "template_path": "/path/to/template.md"
            }
        }