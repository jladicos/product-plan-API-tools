"""
Unit tests for TeamsResource class

Tests teams endpoint and ID-to-name mapping functionality.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.teams import TeamsResource


class TestTeamsResourceEndpoint:
    """Test TeamsResource endpoint configuration"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set to 'teams'"""
        resource = TeamsResource()
        assert resource.endpoint_path == "teams"


class TestTeamsResourceBuildMapping:
    """Test TeamsResource.build_id_to_name_mapping() method"""

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_success(self, mock_get_teams):
        """Test successful creation of team ID to name mapping"""
        # Mock teams API response
        mock_get_teams.return_value = {
            "results": [
                {"id": 1, "name": "Engineering"},
                {"id": 2, "name": "Product"},
                {"id": 3, "name": "Design"}
            ],
            "paging": {"next": None}
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        assert mapping == {
            1: "Engineering",
            2: "Product",
            3: "Design"
        }
        assert len(mapping) == 3

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_empty_results(self, mock_get_teams):
        """Test mapping with no teams"""
        mock_get_teams.return_value = {
            "results": [],
            "paging": {"next": None}
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        assert mapping == {}

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_missing_results_key(self, mock_get_teams):
        """Test mapping when API response missing 'results' key"""
        mock_get_teams.return_value = {
            "paging": {"next": None}
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        assert mapping == {}

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_skips_incomplete_teams(self, mock_get_teams):
        """Test that teams missing id or name are skipped"""
        mock_get_teams.return_value = {
            "results": [
                {"id": 1, "name": "Engineering"},
                {"id": 2},  # Missing name
                {"name": "Product"},  # Missing id
                {"id": 3, "name": "Design"}
            ]
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        # Only valid teams should be in mapping
        assert mapping == {
            1: "Engineering",
            3: "Design"
        }
        assert len(mapping) == 2

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_fetches_all_pages(self, mock_get_teams):
        """Test that build_mapping fetches all pages"""
        mock_get_teams.return_value = {
            "results": [{"id": 1, "name": "Team1"}]
        }

        resource = TeamsResource()
        resource.build_id_to_name_mapping()

        # Verify get_teams was called with get_all=True
        mock_get_teams.assert_called_once_with(get_all=True)

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_handles_large_team_set(self, mock_get_teams):
        """Test mapping with many teams"""
        # Create 100 mock teams
        teams = [{"id": i, "name": f"Team{i}"} for i in range(1, 101)]
        mock_get_teams.return_value = {
            "results": teams
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        assert len(mapping) == 100
        assert mapping[1] == "Team1"
        assert mapping[100] == "Team100"

    @patch.object(TeamsResource, 'get_teams')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_build_mapping_preserves_team_names_with_special_chars(self, mock_get_teams):
        """Test that team names with special characters are preserved"""
        mock_get_teams.return_value = {
            "results": [
                {"id": 1, "name": "Engineering & DevOps"},
                {"id": 2, "name": "Product/UX"},
                {"id": 3, "name": "Sales (West Coast)"}
            ]
        }

        resource = TeamsResource()
        mapping = resource.build_id_to_name_mapping()

        assert mapping[1] == "Engineering & DevOps"
        assert mapping[2] == "Product/UX"
        assert mapping[3] == "Sales (West Coast)"


class TestTeamsResourceIntegration:
    """Integration tests using inherited BaseResource methods"""

    @patch.object(TeamsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_get_teams_calls_fetch_list(self, mock_fetch_list):
        """Test that get_teams properly uses inherited fetch_list"""
        mock_fetch_list.return_value = {
            "results": [{"id": 1, "name": "Team1"}]
        }

        resource = TeamsResource()
        result = resource.get_teams(page=2, page_size=50, get_all=False)

        # Should call fetch_list with correct endpoint and parameters
        mock_fetch_list.assert_called_once()
        # The endpoint will be "teams" from endpoint_path property
        assert result["results"][0]["id"] == 1
