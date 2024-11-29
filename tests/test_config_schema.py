# test_config_schema.py
import pytest

from aisignal.core.config_schema import (
    APIKeys,
    AppConfiguration,
    ConfigError,
    ConfigFileError,
    ConfigValidationError,
    ObsidianConfig,
    Prompts,
)


def test_apikeys_missing_keys():
    # Test case where one of the required API keys is missing
    data_missing_jinaai = {"openai": "some-key"}
    data_missing_openai = {"jinaai": "some-key"}

    with pytest.raises(ConfigValidationError) as excinfo:
        APIKeys.from_dict(data_missing_jinaai)
    assert "Missing required API keys: {'jinaai'}" in str(excinfo.value)

    with pytest.raises(ConfigValidationError) as excinfo:
        APIKeys.from_dict(data_missing_openai)
    assert "Missing required API keys: {'openai'}" in str(excinfo.value)


def test_apikeys_no_missing_keys():
    # Test case where all required API keys are provided
    valid_data = {"jinaai": "some-key", "openai": "some-key"}

    try:
        api_keys = APIKeys.from_dict(valid_data)
        assert api_keys.jinaai == "some-key"
        assert api_keys.openai == "some-key"
    except ConfigValidationError:
        pytest.fail("ConfigValidationError was raised unexpectedly!")


def test_obsidian_config_missing_vault_path():
    # Test case where 'vault_path' is missing
    data_missing_vault_path = {"template_path": "some-path.md"}

    with pytest.raises(ConfigValidationError) as excinfo:
        ObsidianConfig.from_dict(data_missing_vault_path)
    assert "Obsidian configuration missing vault_path" in str(excinfo.value)


def test_obsidian_config_no_missing_vault_path():
    # Test case where 'vault_path' is provided
    valid_data = {
        "vault_path": "/path/to/vault",
        "template_path": "/path/to/template.md",
    }

    try:
        obsidian_config = ObsidianConfig.from_dict(valid_data)
        assert obsidian_config.vault_path == "/path/to/vault"
        assert obsidian_config.template_path == "/path/to/template.md"
    except ConfigValidationError:
        pytest.fail("ConfigValidationError was raised unexpectedly!")


def test_apikeys_to_dict():
    # Test APIKeys to_dict method
    api_keys = APIKeys(jinaai="jina-key", openai="openai-key")
    expected_dict = {"jinaai": "jina-key", "openai": "openai-key"}

    result = api_keys.to_dict()
    assert result == expected_dict, f"Expected {expected_dict}, but got {result}"


def test_obsidian_config_to_dict():
    # Test ObsidianConfig to_dict method
    obsidian_config = ObsidianConfig(
        vault_path="/path/to/vault", template_path="/path/to/template.md"
    )
    expected_dict = {
        "vault_path": "/path/to/vault",
        "template_path": "/path/to/template.md",
    }

    result = obsidian_config.to_dict()
    assert result == expected_dict, f"Expected {expected_dict}, but got {result}"


# To ensure that optional fields are handled:
def test_obsidian_config_to_dict_no_template():
    # Test ObsidianConfig to_dict method with no template_path
    obsidian_config = ObsidianConfig(vault_path="/path/to/vault")
    expected_dict = {"vault_path": "/path/to/vault", "template_path": None}

    result = obsidian_config.to_dict()
    assert result == expected_dict, f"Expected {expected_dict}, but got {result}"


def test_prompts_from_dict_missing_content_extraction():
    # Test case where 'content_extraction' is missing
    data_missing_content_extraction = {}

    with pytest.raises(ConfigValidationError) as excinfo:
        Prompts.from_dict(data_missing_content_extraction)
    assert "Missing content_extraction prompt" in str(excinfo.value)


def test_prompts_from_dict_no_missing_content_extraction():
    # Test case where 'content_extraction' is provided
    valid_data = {"content_extraction": "Extract this content"}

    try:
        prompts = Prompts.from_dict(valid_data)
        assert prompts.content_extraction == "Extract this content"
    except ConfigValidationError:
        pytest.fail("ConfigValidationError was raised unexpectedly!")


def test_get_default_config_structure():
    # Define the expected keys in the default configuration
    expected_keys = {"categories", "sources", "api_keys", "prompts", "obsidian"}

    # Get the default configuration
    default_config = AppConfiguration.get_default_config()

    # Check if all expected keys are present in the default configuration
    for key in expected_keys:
        assert (
            key in default_config
        ), f"Key '{key}' is missing from the default configuration"


def test_appconfiguration_from_dict_missing_key():
    # Define a sample dictionary missing one of the required keys
    incomplete_data = {
        "categories": ["AI", "Programming"],
        "sources": ["https://example.com"],
        # "api_keys" key is missing
        "prompts": {"content_extraction": "Extract this content"},
        "obsidian": {"vault_path": "/path/to/vault"},
    }

    # Attempt to create an AppConfiguration and expect a ConfigValidationError
    with pytest.raises(ConfigValidationError) as excinfo:
        AppConfiguration.from_dict(incomplete_data)
    assert "Missing required configuration key" in str(excinfo.value)


def test_appconfiguration_load_yaml_error(tmp_path):
    # Write an intentional malformed YAML to a temporary file
    invalid_yaml_content = """
    categories
      - AI
      - Programming
    sources:
      - https://example.com
    """
    invalid_yaml_path = tmp_path / "invalid_config.yaml"
    invalid_yaml_path.write_text(invalid_yaml_content)

    # Test for ConfigFileError specifically
    with pytest.raises(ConfigError) as excinfo:
        AppConfiguration.load(invalid_yaml_path)
    assert "Failed to load configuration due to YAML error" in str(excinfo.value)


def test_appconfiguration_load_yaml_parser_error(tmp_path):
    # Create a YAML string that is intentionally malformed
    malformed_yaml_content = """
    categories: [AI, Programming
    sources:
      - https://example.com
    """

    # Create a temporary file and write the malformed YAML content to it
    malformed_yaml_path = tmp_path / "malformed_config.yaml"
    malformed_yaml_path.write_text(malformed_yaml_content)

    # Test that loading this file raises a ConfigFileError due to yaml.ParserError
    with pytest.raises(ConfigError) as excinfo:
        AppConfiguration.load(malformed_yaml_path)

    # Check that the exception message indicates a parsing error
    assert "Invalid YAML in configuration file" in str(excinfo.value)
