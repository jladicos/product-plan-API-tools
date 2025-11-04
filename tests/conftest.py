"""
Shared pytest fixtures for ProductPlan API tests
"""
import pytest
import json
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_token():
    """Return a mock API token for testing"""
    return "test_token_1234567890abcdef"


@pytest.fixture
def sample_ideas_response(fixtures_dir):
    """Load sample ideas API response from fixture"""
    fixture_file = fixtures_dir / "ideas_response.json"
    if fixture_file.exists():
        with open(fixture_file, 'r') as f:
            return json.load(f)
    # Default minimal response if fixture doesn't exist yet
    return {
        "results": [
            {
                "id": 1,
                "name": "Test Idea 1",
                "description": "Test description",
                "location_status": "visible"
            }
        ],
        "paging": {
            "page": 1,
            "page_size": 200,
            "total": 1,
            "next": None
        }
    }


@pytest.fixture
def sample_teams_response(fixtures_dir):
    """Load sample teams API response from fixture"""
    fixture_file = fixtures_dir / "teams_response.json"
    if fixture_file.exists():
        with open(fixture_file, 'r') as f:
            return json.load(f)
    # Default minimal response if fixture doesn't exist yet
    return {
        "results": [
            {"id": 1, "name": "Team A"},
            {"id": 2, "name": "Team B"}
        ],
        "paging": {
            "page": 1,
            "page_size": 200,
            "total": 2,
            "next": None
        }
    }


@pytest.fixture
def sample_okrs_response(fixtures_dir):
    """Load sample OKRs API response from fixture"""
    fixture_file = fixtures_dir / "okrs_response.json"
    if fixture_file.exists():
        with open(fixture_file, 'r') as f:
            return json.load(f)
    # Default minimal response if fixture doesn't exist yet
    return {
        "results": [
            {
                "id": 1,
                "name": "Test Objective",
                "description": "Test objective description",
                "location_status": "active",
                "team_ids": [1]
            }
        ],
        "paging": {
            "page": 1,
            "page_size": 200,
            "total": 1,
            "next": None
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test output files"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir
