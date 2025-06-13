from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from aisignal.core.config import ConfigManager
from aisignal.core.config_schema import ConfigError


@pytest.fixture
def sample_config():
    return {
        "api_keys": {"openai": "test-openai-key", "jinaai": "test-jina-key"},
        "categories": ["news", "research"],
        "sources": ["source1", "source2"],
        "obsidian": {
            "vault_path": "/path/to/vault",
            "template_path": "/path/to/template",
        },
        "prompts": {"content_extraction": "test prompt"},
        "sync_interval": 24,
        "min_threshold": 50.0,
        "max_threshold": 80.0,
    }


@pytest.fixture
def mock_config_file(sample_config):
    return yaml.safe_dump(sample_config)


def test_init_default_path(sample_config, mock_config_file):
    with patch("pathlib.Path.home") as mock_home, patch(
        "pathlib.Path.exists"
    ) as mock_exists, patch("builtins.open", mock_open(read_data=mock_config_file)):
        mock_home.return_value = Path("/home/user")
        mock_exists.return_value = True

        config_manager = ConfigManager()
        assert config_manager.config_path == Path(
            "/home/user/.config/aisignal/config.yaml"
        )


def test_init_custom_path(sample_config, mock_config_file):
    custom_path = Path("/custom/path/config.yaml")
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open", mock_open(read_data=mock_config_file)
    ):
        mock_exists.return_value = True

        config_manager = ConfigManager(custom_path)
        assert config_manager.config_path == custom_path


def test_load_config(mock_config_file, sample_config):
    custom_path = Path("test.yaml")
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open", mock_open(read_data=mock_config_file)
    ):
        mock_exists.return_value = True
        config_manager = ConfigManager(custom_path)

        assert config_manager.categories == sample_config["categories"]
        assert config_manager.sources == sample_config["sources"]
        assert config_manager.openai_api_key == sample_config["api_keys"]["openai"]
        assert config_manager.jina_api_key == sample_config["api_keys"]["jinaai"]
        assert (
            config_manager.obsidian_vault_path
            == sample_config["obsidian"]["vault_path"]
        )
        assert (
            config_manager.obsidian_template_path
            == sample_config["obsidian"]["template_path"]
        )
        assert (
            config_manager.content_extraction_prompt
            == sample_config["prompts"]["content_extraction"]
        )


def test_save_config(mock_config_file, sample_config):
    mock_file = mock_open(read_data=mock_config_file)
    mock_file.return_value.write = MagicMock()  # Add explicit write mock
    with (
        patch("builtins.open", mock_file),
        patch("pathlib.Path.mkdir") as mock_mkdir,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = True
        config_manager = ConfigManager(Path("test.yaml"))
        config_manager.save(sample_config)

        # Verify directory creation
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify file writing
        # Get the written data from the second call (write operation)
        write_calls = mock_file.return_value.write.call_args_list
        written_data = "".join(call[0][0] for call in write_calls)
        written_config = yaml.safe_load(written_data)

        # Verify config content
        assert written_config["api_keys"] == sample_config["api_keys"]
        assert written_config["categories"] == sample_config["categories"]
        assert written_config["sources"] == sample_config["sources"]
        assert written_config["obsidian"] == sample_config["obsidian"]
        assert written_config["prompts"] == sample_config["prompts"]


def test_missing_config_file():
    with pytest.raises(ConfigError):
        ConfigManager(Path("nonexistent.yaml"))


def test_invalid_yaml():
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content")):
        with pytest.raises(ConfigError):
            ConfigManager(Path("test.yaml"))


def test_missing_required_fields(mock_config_file):
    invalid_config = {"api_keys": {"openai": "key"}}  # Missing required fields
    with patch("builtins.open", mock_open(read_data=yaml.safe_dump(invalid_config))):
        with pytest.raises(ConfigError):
            ConfigManager(Path("test.yaml"))
