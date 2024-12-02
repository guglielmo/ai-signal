from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from yaml.parser import ParserError


class ConfigError(Exception):
    """
    Custom exception class for configuration-related errors.

    This exception is raised when there is an issue with program configuration,
    such as missing configuration files, invalid configuration values, or other
    configuration-related problems.

    It can be used to signal errors during the loading or parsing of configuration
    data, enabling the calling code to handle these specific types of errors
    appropriately.
    """

    pass


class ConfigValidationError(ConfigError):
    """
    Represents an error that occurs during configuration validation.

    ConfigValidationError is a subclass of ConfigError and is used to signal
    issues that arise specifically from validating configuration inputs. It can
    be used to distinguish configuration validation errors from other types of
    configuration errors.
    """

    pass


class ConfigFileError(ConfigError):
    """
    ConfigFileError is an exception class that inherits from ConfigError.

    This exception is raised when an error related to a configuration
    file is encountered, such as when the file is missing, unreadable,
    or malformed. It provides a mechanism to distinguish errors
    specifically associated with configuration files from other types
    of configuration errors.

    Attributes and methods inherited from ConfigError are applicable.
    """

    pass


@dataclass
class APIKeys:
    """
    Represents API keys for services, encapsulating 'jinaai' and 'openai' keys.

    Attributes:
      jinaai (str): API key for the Jina AI service.
      openai (str): API key for the OpenAI service.
    """

    jinaai: str
    openai: str

    @classmethod
    def from_dict(cls, data: Dict) -> "APIKeys":
        """
        Creates an APIKeys instance from a dictionary, verifying necessary keys.

        :param data: A dictionary containing API key information.
        :type data: Dict
        :raises ConfigValidationError: If any required API keys are missing.
        :return: An instance of APIKeys with keys initialized from the dictionary.
        :rtype: APIKeys
        """
        required_keys = {"jinaai", "openai"}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ConfigValidationError(f"Missing required API keys: {missing_keys}")
        return cls(**{k: data[k] for k in required_keys})

    def to_dict(self):
        """
        Converts the instance attributes to a dictionary representation.

        The resulting dictionary contains the keys 'jinaai' and 'openai', which
        correspond to the values of the instance's `jinaai` and `openai` attributes.

        :return: A dictionary with keys 'jinaai' and 'openai' mapping to their
         respective attribute values.
        """
        return {"jinaai": self.jinaai, "openai": self.openai}


@dataclass
class ObsidianConfig:
    """
    Represents the configuration for an Obsidian vault.

    Attributes:
      vault_path (str): The file path to the Obsidian vault directory.
      template_path (Optional[str]): The file path to the template directory,
        if any.

    Methods:
      from_dict(data): Class method to create an instance of ObsidianConfig
        from a dictionary.
      to_dict(): Converts the ObsidianConfig instance to a dictionary
        representation.
    """

    vault_path: str
    template_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "ObsidianConfig":
        """
        Creates an instance of ObsidianConfig from a dictionary representation.

        :param data: A dictionary containing configuration data. Must include the
          'vault_path' key.
        :raises ConfigValidationError: If 'vault_path' is not present in the data.
        :return: An instance of ObsidianConfig initialized with the provided data.
        """
        if "vault_path" not in data:
            raise ConfigValidationError("Obsidian configuration missing vault_path")
        return cls(**data)

    def to_dict(self):
        """
        Converts the object's attributes to a dictionary representation.

        :return: A dictionary containing 'vault_path' and 'template_path' as keys,
         with their corresponding attribute values.
        :rtype: dict
        """
        return {
            "vault_path": self.vault_path,
            "template_path": self.template_path,
        }


@dataclass
class Prompts:
    """
    Represents a collection of prompt strings with specific functionalities for data
    conversion.

    Attributes:
      content_extraction (str): A string representing prompt content extraction logic.
    """

    content_extraction: str

    @classmethod
    def from_dict(cls, data: Dict) -> "Prompts":
        """
        Creates an instance of the `Prompts` class from a dictionary. Ensures that
        the dictionary contains a key for "content_extraction", raising an error
        if it is absent.

        :param data: A dictionary containing the initialization parameters for the
          Prompts object. Must include a key "content_extraction".
        :type data: Dict
        :return: An instance of the `Prompts` class.
        :rtype: Prompts
        :raises ConfigValidationError: If "content_extraction" key is missing in
          the provided dictionary.
        """
        if "content_extraction" not in data:
            raise ConfigValidationError("Missing content_extraction prompt")
        return cls(**data)

    def to_dict(self):
        """
        Converts the instance attributes to a dictionary format.

        :return: A dictionary with keys corresponding to the attribute names
                 and values corresponding to the attribute values. In this
                 case, it returns the dictionary with the key "content_extraction"
                 mapped to its respective value.
        """
        return {
            "content_extraction": self.content_extraction,
        }


@dataclass
class AppConfiguration:
    """
    AppConfiguration is a data class that holds configuration details for the
    application, including categories, sources, API keys, prompts,
    and Obsidian configuration.

    Methods:
      from_dict: Class method to instantiate AppConfiguration from a dictionary.
      load: Class method to load and validate configuration from a file.
      get_default_config: Class method to return the default configuration structure.
    """

    categories: List[str]
    sources: List[str]
    api_keys: APIKeys
    prompts: Prompts
    obsidian: ObsidianConfig
    sync_interval: int = 24
    min_threshold: float = 50.0  # Default value
    max_threshold: float = 80.0  # Default value

    @classmethod
    def from_dict(cls, data: Dict) -> "AppConfiguration":
        """
        Creates an instance of `AppConfiguration` from a dictionary of configuration
        data. Extracts values for categories, sources, api_keys, prompts, and obsidian
        from the provided data. Converts sub-dictionaries to their respective
        configuration objects.

        :param data: A dictionary containing configuration keys and their corresponding
          values.

        :raises ConfigValidationError: If a required configuration key is missing from
          the provided data.

        :return: An instance of `AppConfiguration` populated with values from the input
          dictionary.
        """
        try:
            return cls(
                categories=data["categories"],
                sources=data["sources"],
                api_keys=APIKeys.from_dict(data["api_keys"]),
                prompts=Prompts.from_dict(data["prompts"]),
                obsidian=ObsidianConfig.from_dict(data["obsidian"]),
                sync_interval=int(data.get("sync_interval", 24)),
                min_threshold=float(data.get("min_threshold", 50.0)),
                max_threshold=float(data.get("max_threshold", 80.0)),
            )
        except KeyError as e:
            raise ConfigValidationError(f"Missing required configuration key: {e}")

    @classmethod
    def load(cls, config_path: Path) -> "AppConfiguration":
        """
        Loads application configuration from a YAML file.

        :param config_path: Path to the configuration YAML file.
        :type config_path: Path
        :raises ConfigFileError: If the configuration file is not found.
        :raises ConfigError: If there is a parsing error or another YAML
          related error while loading the configuration.
        :return: An instance of AppConfiguration populated with data from
          the configuration file.
        :rtype: AppConfiguration
        """
        if not config_path.exists():
            raise ConfigFileError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
        except ParserError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}")
        except (
            yaml.YAMLError
        ) as e:  # Broad exception, for other non-parsing related YAML errors
            raise ConfigError(f"Failed to load configuration due to YAML error: {e}")

        return cls.from_dict(data)

    @classmethod
    def get_default_config(cls) -> Dict:
        """
        Provides the default configuration settings for the application.

        :return: A dictionary containing default configuration settings
          including categories, sources, API keys, prompts, and Obsidian settings.
        :rtype: Dict
        """
        return {
            "categories": [
                "AI",
                "Programming",
                "Data Science",
                "Machine Learning",
            ],
            "sources": [
                "https://example.com/blog1",
                "https://example.com/blog2",
            ],
            "api_keys": {
                "jinaai": "your-jina-api-key",
                "openai": "your-openai-api-key",
            },
            "prompts": {"content_extraction": "Default prompt for content extraction"},
            "obsidian": {
                "vault_path": "/path/to/your/vault",
                "template_path": "/path/to/template.md",
            },
            "sync_interval": 24,
            "min_threshold": 50.0,
            "max_threshold": 80.0,
        }
