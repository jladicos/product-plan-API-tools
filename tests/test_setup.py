"""
Basic test to verify pytest setup is working
"""
import pytest


def test_pytest_working():
    """Verify pytest is installed and working"""
    assert True


def test_fixtures_available(mock_token, fixtures_dir):
    """Verify shared fixtures are available"""
    assert mock_token == "test_token_1234567890abcdef"
    assert fixtures_dir.exists()
    assert fixtures_dir.name == "fixtures"


def test_temp_output_dir(temp_output_dir):
    """Verify temp output directory fixture works"""
    assert temp_output_dir.exists()
    assert temp_output_dir.is_dir()

    # Test we can write to it
    test_file = temp_output_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.read_text() == "test content"
