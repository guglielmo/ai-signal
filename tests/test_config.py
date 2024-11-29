import pytest
from pathlib import Path
from aisignal.utils.config import load_config, ensure_config

def test_load_config():
    """Test configuration loading."""
    config = load_config()
    assert "sources" in config
    assert "api_keys" in config

def test_missing_config():
    """Test handling of missing config file."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.yaml"))
