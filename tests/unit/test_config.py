"""
Unit tests for config module

Tests configuration loading and validation from env/.env file.

Note: The config module calls _load_environment() on import, which loads
the real env/.env file. This means tests must use patch.dict(os.environ)
to override values, as the real .env file is loaded before tests can intervene.
Some edge cases (like simulating missing env vars when real .env exists) are
covered by integration tests instead.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestConfigModule:
    """Tests for configuration module"""

    def test_get_api_token_returns_value_from_env(self):
        """Test get_api_token() returns value from environment"""
        with patch.dict(os.environ, {'PRODUCTPLAN_API_TOKEN': 'test_token_123'}):
            # Re-import to get fresh module with mocked env
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            token = config.get_api_token()
            assert token == 'test_token_123'

    def test_get_api_token_strips_whitespace(self):
        """Test get_api_token() strips leading/trailing whitespace"""
        with patch.dict(os.environ, {'PRODUCTPLAN_API_TOKEN': '  test_token_123  '}):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            token = config.get_api_token()
            assert token == 'test_token_123'

    def test_get_api_token_error_when_not_set(self):
        """Test get_api_token() raises ValueError when not set"""
        with patch.dict(os.environ, {'PRODUCTPLAN_API_TOKEN': ''}, clear=True):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_api_token()

            assert 'PRODUCTPLAN_API_TOKEN is required' in str(exc_info.value)
            assert 'env/.env' in str(exc_info.value)

    def test_get_api_token_error_when_only_whitespace(self):
        """Test get_api_token() raises ValueError when only whitespace"""
        with patch.dict(os.environ, {'PRODUCTPLAN_API_TOKEN': '   '}):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_api_token()

            assert 'PRODUCTPLAN_API_TOKEN is required' in str(exc_info.value)

    def test_get_url_prefix_returns_value_from_env(self):
        """Test get_url_prefix() returns value from environment"""
        test_url = 'https://app.productplan.com/discovery/ideas/'
        with patch.dict(os.environ, {'PRODUCTPLAN_URL_PREFIX': test_url}):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            url_prefix = config.get_url_prefix()
            assert url_prefix == test_url

    def test_get_url_prefix_strips_whitespace(self):
        """Test get_url_prefix() strips leading/trailing whitespace"""
        test_url = 'https://app.productplan.com/discovery/ideas/'
        with patch.dict(os.environ, {'PRODUCTPLAN_URL_PREFIX': f'  {test_url}  '}):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            url_prefix = config.get_url_prefix()
            assert url_prefix == test_url

    def test_get_url_prefix_error_when_not_set(self):
        """Test get_url_prefix() raises ValueError when not set"""
        with patch.dict(os.environ, {'PRODUCTPLAN_URL_PREFIX': ''}, clear=True):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_url_prefix()

            assert 'PRODUCTPLAN_URL_PREFIX is required' in str(exc_info.value)
            assert 'env/.env' in str(exc_info.value)

    def test_get_google_sheets_config_returns_complete_config(self, tmp_path):
        """Test get_google_sheets_config() returns dict when fully configured"""
        # Create a temporary credentials file
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text('{"test": "data"}')

        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': str(creds_file),
            'GOOGLE_SHEET_ID': 'test_sheet_id_123',
            'GOOGLE_SHEET_NAME': 'SLA Tracking'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            result = config.get_google_sheets_config()

            assert result is not None
            assert result['credentials_file'] == str(creds_file)
            assert result['sheet_id'] == 'test_sheet_id_123'
            assert result['sheet_name'] == 'SLA Tracking'

    def test_get_google_sheets_config_returns_none_when_not_configured(self):
        """Test get_google_sheets_config() returns None when no config set"""
        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': '',
            'GOOGLE_SHEET_ID': '',
            'GOOGLE_SHEET_NAME': ''
        }

        with patch.dict(os.environ, env_vars, clear=True):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            result = config.get_google_sheets_config()
            assert result is None

    def test_get_google_sheets_config_error_on_partial_config_missing_credentials(self):
        """Test get_google_sheets_config() errors when credentials missing"""
        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': '',
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SHEET_NAME': 'SLA Tracking'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_google_sheets_config()

            assert 'Partial Google Sheets configuration' in str(exc_info.value)
            assert 'All three' in str(exc_info.value)

    def test_get_google_sheets_config_error_on_partial_config_missing_sheet_id(self):
        """Test get_google_sheets_config() errors when sheet ID missing"""
        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': '/path/to/creds.json',
            'GOOGLE_SHEET_ID': '',
            'GOOGLE_SHEET_NAME': 'SLA Tracking'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_google_sheets_config()

            assert 'Partial Google Sheets configuration' in str(exc_info.value)

    def test_get_google_sheets_config_error_on_partial_config_missing_sheet_name(self):
        """Test get_google_sheets_config() errors when sheet name missing"""
        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': '/path/to/creds.json',
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SHEET_NAME': ''
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_google_sheets_config()

            assert 'Partial Google Sheets configuration' in str(exc_info.value)

    def test_get_google_sheets_config_error_on_missing_credentials_file(self):
        """Test get_google_sheets_config() errors when credentials file doesn't exist"""
        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': '/nonexistent/path/credentials.json',
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SHEET_NAME': 'SLA Tracking'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(FileNotFoundError) as exc_info:
                config.get_google_sheets_config()

            assert 'Google credentials file not found' in str(exc_info.value)
            assert '/nonexistent/path/credentials.json' in str(exc_info.value)

    def test_get_google_sheets_config_error_when_credentials_is_directory(self, tmp_path):
        """Test get_google_sheets_config() errors when credentials path is a directory"""
        # Create a directory instead of a file
        creds_dir = tmp_path / "credentials"
        creds_dir.mkdir()

        env_vars = {
            'GOOGLE_CREDENTIALS_FILE': str(creds_dir),
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SHEET_NAME': 'SLA Tracking'
        }

        with patch.dict(os.environ, env_vars):
            import importlib
            import productplan_api_tools.config as config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.get_google_sheets_config()

            assert 'not a file' in str(exc_info.value)
            assert str(creds_dir) in str(exc_info.value)

    def test_module_import_fails_when_env_file_missing(self):
        """Test that module import fails when env/.env doesn't exist"""
        # Mock os.path.exists to return False for env/.env
        with patch('productplan_api_tools.config.os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                import importlib
                import productplan_api_tools.config as config
                importlib.reload(config)

            assert 'Configuration file not found' in str(exc_info.value)
            assert 'env/.env' in str(exc_info.value)
            assert 'env/.env.sample' in str(exc_info.value)
