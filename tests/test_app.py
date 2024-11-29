# test_app.py

import pytest
from unittest.mock import Mock, patch
from aisignal.app import ContentCuratorApp


@patch('aisignal.app.ConfigManager')
@patch('aisignal.app.ResourceFilterState')
@patch('aisignal.app.ResourceManager')
@patch('aisignal.app.MarkdownSourceStorage')
@patch('aisignal.app.ParsedItemStorage')
@patch('aisignal.app.ContentService')
@patch('aisignal.app.ExportManager')
def test_content_curator_app_initialization(
        mock_export_manager,
        mock_content_service,
        mock_parsed_item_storage,
        mock_markdown_storage,
        mock_resource_manager,
        mock_filter_state,
        mock_config_manager
):
    # Setup mocks and their return values if needed
    mock_config_manager.return_value.jina_api_key = 'dummy_key'
    mock_config_manager.return_value.openai_api_key = 'dummy_key'
    mock_config_manager.return_value.categories = ['cat1', 'cat2']
    mock_config_manager.return_value.obsidian_vault_path = '/path/to/vault'
    mock_config_manager.return_value.obsidian_template_path = '/path/to/template'

    # Create instance of the app
    app = ContentCuratorApp()

    # Assert the mocks were called, verifying initialization
    mock_config_manager.assert_called_once_with(None)
    mock_filter_state.assert_called_once()
    mock_resource_manager.assert_called_once()
    mock_markdown_storage.assert_called_once()
    mock_parsed_item_storage.assert_called_once()
    mock_content_service.assert_called_once_with(
        jina_api_key='dummy_key',
        openai_api_key='dummy_key',
        categories=['cat1', 'cat2'],
        markdown_storage=app.markdown_storage,
        item_storage=app.item_storage,
    )
    mock_export_manager.assert_called_once_with(
        '/path/to/vault',
        '/path/to/template'
    )


def test_notify_user():
    app = ContentCuratorApp()
    app.notify = Mock()

    # Call the method
    app.notify_user("Test message")

    # Verify the notify method is called with the message
    app.notify.assert_called_with("Test message")

@patch('aisignal.app.ContentCuratorApp.log', new_callable=Mock)
def test_handle_error(mock_log):
    app = ContentCuratorApp()
    app.notify_user = Mock()

    # Call the method with and without an error
    app.handle_error("Test error")
    app.handle_error("Test error", Exception("Details"))

    # Verify logging and notification behavior
    mock_log.error.assert_any_call("Test error")
    mock_log.error.assert_any_call("Test error: Details")
    app.notify_user.assert_any_call("Error: Test error")


