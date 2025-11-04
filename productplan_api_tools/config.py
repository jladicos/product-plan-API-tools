"""
Configuration Module

Central configuration management for ProductPlan API Tools.
Loads and validates configuration from env/.env file.

This module loads configuration on import and fails fast if configuration
is missing or invalid. Use the provided getter functions to access config values.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv


# Path to .env file (relative to project root)
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env', '.env')


def _load_environment():
    """
    Load environment variables from env/.env file

    Called automatically on module import.
    Fails fast if env/.env file doesn't exist.

    Raises:
        FileNotFoundError: If env/.env file is not found
    """
    if not os.path.exists(ENV_FILE_PATH):
        raise FileNotFoundError(
            f"Configuration file not found: {ENV_FILE_PATH}\n"
            f"Please copy env/.env.sample to env/.env and fill in your values."
        )

    # Load .env file into environment variables
    load_dotenv(ENV_FILE_PATH)


def get_api_token() -> str:
    """
    Get ProductPlan API token from configuration

    Returns:
        API token string

    Raises:
        ValueError: If PRODUCTPLAN_API_TOKEN is not set in env/.env
    """
    token = os.getenv('PRODUCTPLAN_API_TOKEN', '').strip()

    if not token:
        raise ValueError(
            "Error: PRODUCTPLAN_API_TOKEN is required but not set in env/.env. "
            "Please copy env/.env.sample to env/.env and fill in your API token."
        )

    return token


def get_url_prefix() -> str:
    """
    Get ProductPlan URL prefix for generating idea links

    Returns:
        URL prefix string (e.g., "https://app.productplan.com/discovery/ideas/")

    Raises:
        ValueError: If PRODUCTPLAN_URL_PREFIX is not set in env/.env
    """
    url_prefix = os.getenv('PRODUCTPLAN_URL_PREFIX', '').strip()

    if not url_prefix:
        raise ValueError(
            "Error: PRODUCTPLAN_URL_PREFIX is required but not set in env/.env. "
            "Please copy env/.env.sample to env/.env and fill in your URL prefix."
        )

    return url_prefix


def get_google_sheets_config() -> Optional[Dict[str, str]]:
    """
    Get Google Sheets configuration

    Returns:
        Dictionary with keys: 'credentials_file', 'sheet_id', 'sheet_name'
        Returns None if no Google Sheets configuration is set

    Raises:
        ValueError: If partial Google Sheets configuration is detected
                   (some variables set but not all)
        FileNotFoundError: If credentials file path is set but file doesn't exist
    """
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', '').strip()
    sheet_id = os.getenv('GOOGLE_SHEET_ID', '').strip()
    sheet_name = os.getenv('GOOGLE_SHEET_NAME', '').strip()

    # Count how many are set
    set_count = sum([bool(credentials_file), bool(sheet_id), bool(sheet_name)])

    # If none are set, Google Sheets is not configured (valid state)
    if set_count == 0:
        return None

    # If some but not all are set, this is an error (partial configuration)
    if set_count != 3:
        raise ValueError(
            "Error: Partial Google Sheets configuration detected. "
            "All three Google Sheets variables must be set or none."
        )

    # All three are set - validate credentials file exists and is a file (not directory)
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(
            f"Error: Google credentials file not found: {credentials_file}\n"
            f"Please ensure GOOGLE_CREDENTIALS_FILE in env/.env points to a valid file."
        )

    if not os.path.isfile(credentials_file):
        raise ValueError(
            f"Error: Google credentials path is not a file: {credentials_file}\n"
            f"Please ensure GOOGLE_CREDENTIALS_FILE in env/.env points to a file, not a directory."
        )

    return {
        'credentials_file': credentials_file,
        'sheet_id': sheet_id,
        'sheet_name': sheet_name
    }


def get_runs_sheet_name() -> str:
    """
    Get the name of the Runs tracking sheet/tab

    This sheet tracks audit trail for sla-init and sla-update executions.

    Returns:
        Sheet name for runs tracking (default: "Runs")
    """
    return os.getenv('GOOGLE_SHEET_RUNS_NAME', 'Runs').strip() or 'Runs'


# Load environment on module import (fail fast)
_load_environment()
