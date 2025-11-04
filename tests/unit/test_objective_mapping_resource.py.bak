"""
Unit tests for ObjectiveMappingResource class

Tests Cartesian product mapping between company and team objectives.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.objective_maps import ObjectiveMappingResource


class TestObjectiveMappingResourceEndpoint:
    """Test ObjectiveMappingResource endpoint configuration"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set"""
        resource = ObjectiveMappingResource()
        assert resource.endpoint_path == "strategy/objectives"


class TestObjectiveMappingResourceFetchMappingData:
    """Test ObjectiveMappingResource.fetch_mapping_data() method"""

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_basic_cartesian_product(self, mock_fetch_list):
        """Test basic Cartesian product creation"""
        # 2 company objectives (no team_ids)
        # 2 team objectives (with team_ids)
        # Should produce 2 × 2 = 4 mapping rows
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company Obj 1", "team_ids": []},
                {"id": 2, "name": "Company Obj 2", "team_ids": []},
                {"id": 3, "name": "Team Obj 1", "team_ids": [10]},
                {"id": 4, "name": "Team Obj 2", "team_ids": [20]}
            ]
        }

        team_mapping = {10: "Engineering", 20: "Product"}

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        # Should have 4 mapping rows
        assert len(results) == 4

        # Verify structure
        assert all("company_objective_name" in r for r in results)
        assert all("team_objective_name" in r for r in results)
        assert all("team_name" in r for r in results)

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_separates_company_vs_team(self, mock_fetch_list):
        """Test that objectives are correctly separated by team_ids presence"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": []},
                {"id": 2, "name": "Team 1", "team_ids": [10]},
                {"id": 3, "name": "Company 2"},  # Missing team_ids key
                {"id": 4, "name": "Team 2", "team_ids": [20]}
            ]
        }

        team_mapping = {10: "Eng", 20: "Prod"}

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        # 2 company × 2 team = 4 rows
        assert len(results) == 4

        # Verify all company objectives appear
        company_names = [r["company_objective_name"] for r in results]
        assert "Company 1" in company_names
        assert "Company 2" in company_names

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_team_name_resolution(self, mock_fetch_list):
        """Test that team IDs are resolved to team names"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": []},
                {"id": 2, "name": "Team 1", "team_ids": [10]}
            ]
        }

        team_mapping = {10: "Engineering Team"}

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        assert results[0]["team_name"] == "Engineering Team"

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_multiple_teams_per_objective(self, mock_fetch_list):
        """Test handling of objectives with multiple teams"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": []},
                {"id": 2, "name": "Team 1", "team_ids": [10, 20]}
            ]
        }

        team_mapping = {10: "Engineering", 20: "Product"}

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        # Team names should be comma-separated
        assert results[0]["team_name"] == "Engineering, Product"

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_no_company_objectives(self, mock_fetch_list):
        """Test when there are no company-level objectives"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Team 1", "team_ids": [10]},
                {"id": 2, "name": "Team 2", "team_ids": [20]}
            ]
        }

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping={})

        # No company objectives = no mappings
        assert results == []

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_no_team_objectives(self, mock_fetch_list):
        """Test when there are no team-level objectives"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": []},
                {"id": 2, "name": "Company 2", "team_ids": []}
            ]
        }

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping={})

        # No team objectives = no mappings
        assert results == []

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_status_filtering_active(self, mock_fetch_list):
        """Test status filtering for active objectives"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": [], "location_status": "active"},
                {"id": 2, "name": "Team 1", "team_ids": [10], "location_status": "active"},
                {"id": 3, "name": "Archived", "team_ids": [], "location_status": "archived"}
            ]
        }

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(status_filter="active", team_mapping={})

        # Should exclude archived objective
        names = [r["company_objective_name"] for r in results]
        assert "Archived" not in names

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_status_filtering_all(self, mock_fetch_list):
        """Test status_filter='all' includes all objectives"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Active", "team_ids": [], "location_status": "active"},
                {"id": 2, "name": "Archived", "team_ids": [], "location_status": "archived"},
                {"id": 3, "name": "Team", "team_ids": [10]}
            ]
        }

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(status_filter="all", team_mapping={})

        # Should include both company objectives
        company_names = {r["company_objective_name"] for r in results}
        assert "Active" in company_names
        assert "Archived" in company_names

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_unknown_team_id(self, mock_fetch_list):
        """Test handling of team IDs not in mapping"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Company 1", "team_ids": []},
                {"id": 2, "name": "Team 1", "team_ids": [999]}  # Unknown team ID
            ]
        }

        team_mapping = {10: "Engineering"}  # Doesn't include 999

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        # Should still create mapping but team_name will be "Unknown Team"
        assert len(results) == 1
        assert "Unknown Team" in results[0]["team_name"] or results[0]["team_name"] == ""

    @patch.object(ObjectiveMappingResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_mapping_large_cartesian_product(self, mock_fetch_list):
        """Test large Cartesian product (5 company × 10 team = 50 rows)"""
        company_objs = [{"id": i, "name": f"Company {i}", "team_ids": []} for i in range(1, 6)]
        team_objs = [{"id": i+100, "name": f"Team {i}", "team_ids": [i]} for i in range(1, 11)]

        mock_fetch_list.return_value = {
            "results": company_objs + team_objs
        }

        team_mapping = {i: f"Team {i}" for i in range(1, 11)}

        resource = ObjectiveMappingResource()
        results = resource.fetch_mapping_data(team_mapping=team_mapping)

        # Should have 5 × 10 = 50 mapping rows
        assert len(results) == 50
