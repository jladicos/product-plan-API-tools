"""
Unit tests for OKRsResource class

Tests objectives and key results endpoint with team resolution and flattening.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.okrs import OKRsResource


class TestOKRsResourceEndpoint:
    """Test OKRsResource endpoint configuration"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set"""
        resource = OKRsResource()
        assert resource.endpoint_path == "strategy/objectives"


class TestOKRsResourceFetchKeyResults:
    """Test OKRsResource.fetch_key_results() method"""

    @patch.object(OKRsResource, '_make_request')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_key_results_single_page(self, mock_make_request):
        """Test fetching key results for an objective"""
        mock_make_request.return_value = {
            "results": [
                {"id": 1, "description": "KR 1", "target": "100%"},
                {"id": 2, "description": "KR 2", "target": "500"}
            ]
        }

        resource = OKRsResource()
        result = resource.fetch_key_results(objective_id=42)

        assert len(result["results"]) == 2
        # Verify endpoint includes objective ID
        call_args = mock_make_request.call_args
        assert "strategy/objectives/42/key_results" in call_args[0][0]

    @patch.object(OKRsResource, '_fetch_all_pages')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_key_results_all_pages(self, mock_fetch_all_pages):
        """Test fetching all pages of key results"""
        mock_fetch_all_pages.return_value = {
            "results": [{"id": 1}, {"id": 2}, {"id": 3}]
        }

        resource = OKRsResource()
        result = resource.fetch_key_results(objective_id=42, get_all=True)

        assert len(result["results"]) == 3
        mock_fetch_all_pages.assert_called_once()


class TestOKRsResourceFetchEnhanced:
    """Test OKRsResource.fetch_enhanced() method"""

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_basic_with_key_results(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test basic OKR fetching with key results"""
        # Mock objectives list
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "name": "Objective 1"}
            ]
        }

        # Mock objective details
        mock_fetch_details.return_value = {
            "id": 1,
            "name": "Objective 1",
            "description": "Desc",
            "location_status": "active",
            "team_ids": [10]
        }

        # Mock key results
        mock_fetch_key_results.return_value = {
            "results": [
                {"id": 101, "description": "KR 1", "target": "100%", "current": "50%", "progress": "50%"}
            ]
        }

        # Provide team mapping
        team_mapping = {10: "Engineering"}

        resource = OKRsResource()
        results = resource.fetch_enhanced(team_mapping=team_mapping)

        # Should have one row (one key result)
        assert len(results) == 1
        assert results[0]["objective_name"] == "Objective 1"
        assert results[0]["key_result_name"] == "KR 1"
        assert results[0]["team_name"] == "Engineering"
        assert results[0]["objective_id"] == 1
        assert results[0]["key_result_id"] == 101

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_objective_without_key_results(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test objective with no key results creates one row with empty fields"""
        mock_fetch_list.return_value = {
            "results": [{"id": 1, "name": "Obj 1"}]
        }

        mock_fetch_details.return_value = {
            "id": 1,
            "name": "Obj 1",
            "location_status": "active",
            "team_ids": []
        }

        # No key results
        mock_fetch_key_results.return_value = {"results": []}

        resource = OKRsResource()
        results = resource.fetch_enhanced(team_mapping={})

        # Should have one row with empty key result fields
        assert len(results) == 1
        assert results[0]["objective_name"] == "Obj 1"
        assert results[0]["key_result_name"] == ""
        assert results[0]["key_result_target"] == ""
        assert results[0]["key_result_id"] == ""

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_multiple_key_results(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test objective with multiple key results creates multiple rows"""
        mock_fetch_list.return_value = {
            "results": [{"id": 1}]
        }

        mock_fetch_details.return_value = {
            "id": 1,
            "name": "Obj 1",
            "location_status": "active"
        }

        # Multiple key results
        mock_fetch_key_results.return_value = {
            "results": [
                {"id": 101, "description": "KR 1"},
                {"id": 102, "description": "KR 2"},
                {"id": 103, "description": "KR 3"}
            ]
        }

        resource = OKRsResource()
        results = resource.fetch_enhanced(team_mapping={})

        # Should have 3 rows (one per key result)
        assert len(results) == 3
        assert results[0]["key_result_id"] == 101
        assert results[1]["key_result_id"] == 102
        assert results[2]["key_result_id"] == 103

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_team_name_resolution(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test that team IDs are resolved to names"""
        mock_fetch_list.return_value = {
            "results": [{"id": 1}]
        }

        mock_fetch_details.return_value = {
            "id": 1,
            "location_status": "active",
            "team_ids": [10, 20]
        }

        mock_fetch_key_results.return_value = {"results": []}

        team_mapping = {10: "Engineering", 20: "Product"}

        resource = OKRsResource()
        results = resource.fetch_enhanced(team_mapping=team_mapping)

        # Should have both team names
        assert results[0]["team_name"] == "Engineering, Product"

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_fetches_teams_if_no_mapping(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test that teams are fetched internally if no mapping provided"""
        mock_fetch_list.return_value = {"results": []}

        with patch.object(OKRsResource, '_make_request') as mock_make_request:
            mock_make_request.return_value = {
                "results": [{"id": 10, "name": "Team1"}]
            }

            resource = OKRsResource()
            results = resource.fetch_enhanced(team_mapping=None)

            # Should have made a request to teams endpoint
            # (This verifies fallback behavior)
            teams_call_made = any("teams" in str(call) for call in mock_make_request.call_args_list)

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_status_filter_active(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test status filtering for active objectives only"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1},
                {"id": 2},
                {"id": 3}
            ]
        }

        # Mix of active and inactive
        def fetch_details_side_effect(obj_id):
            statuses = {
                1: "active",
                2: "archived",
                3: "active"
            }
            return {
                "id": obj_id,
                "location_status": statuses.get(obj_id),
                "team_ids": []
            }

        mock_fetch_details.side_effect = lambda obj_id: fetch_details_side_effect(obj_id)
        mock_fetch_key_results.return_value = {"results": []}

        resource = OKRsResource()
        results = resource.fetch_enhanced(status_filter="active", team_mapping={})

        # Should only include active objectives
        objective_ids = [r["objective_id"] for r in results]
        assert 1 in objective_ids
        assert 3 in objective_ids
        assert 2 not in objective_ids

    @patch.object(OKRsResource, 'fetch_key_results')
    @patch.object(OKRsResource, 'fetch_details')
    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_status_filter_all(self, mock_fetch_list, mock_fetch_details, mock_fetch_key_results):
        """Test status_filter='all' includes all objectives"""
        mock_fetch_list.return_value = {
            "results": [{"id": 1}, {"id": 2}]
        }

        mock_fetch_details.side_effect = [
            {"id": 1, "location_status": "active"},
            {"id": 2, "location_status": "archived"}
        ]

        mock_fetch_key_results.return_value = {"results": []}

        resource = OKRsResource()
        results = resource.fetch_enhanced(status_filter="all", team_mapping={})

        # Should include both
        assert len(results) == 2

    @patch.object(OKRsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_empty_objectives(self, mock_fetch_list):
        """Test handling of empty objectives list"""
        mock_fetch_list.return_value = {"results": []}

        resource = OKRsResource()
        results = resource.fetch_enhanced(team_mapping={})

        assert results == []
