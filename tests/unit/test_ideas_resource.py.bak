"""
Unit tests for IdeasResource class

Tests ideas endpoint with enhanced detail fetching and location filtering.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.ideas import IdeasResource


class TestIdeasResourceEndpoint:
    """Test IdeasResource endpoint configuration"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set"""
        resource = IdeasResource()
        assert resource.endpoint_path == "discovery/ideas"


class TestIdeasResourceFetchEnhanced:
    """Test IdeasResource.fetch_enhanced() method"""

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_basic(self, mock_fetch_list, mock_fetch_details):
        """Test basic enhanced fetching with detail calls"""
        # Mock list response
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "name": "Idea 1"},
                {"id": 102, "name": "Idea 2"}
            ]
        }

        # Mock detail responses
        mock_fetch_details.side_effect = [
            {"id": 101, "name": "Idea 1", "location_status": "visible", "created_at": "2024-01-01"},
            {"id": 102, "name": "Idea 2", "location_status": "visible", "created_at": "2024-01-02"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced(page=1, page_size=100, get_all=False)

        assert len(results) == 2
        assert results[0]["created_at"] == "2024-01-01"
        assert results[1]["created_at"] == "2024-01-02"

        # Should fetch details for each idea
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_location_status_not_archived(self, mock_fetch_list, mock_fetch_details):
        """Test location_status filtering excludes archived ideas"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101},
                {"id": 102},
                {"id": 103}
            ]
        }

        # Mix of statuses
        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "archived"},
            {"id": 103, "location_status": "hidden"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced(location_status="not_archived")

        # Should exclude archived idea (102)
        assert len(results) == 2
        assert all(r["location_status"] != "archived" for r in results)

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_location_status_archived_only(self, mock_fetch_list, mock_fetch_details):
        """Test location_status filtering for archived ideas only"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101},
                {"id": 102}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "archived"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced(location_status="archived")

        # Should only include archived idea
        assert len(results) == 1
        assert results[0]["id"] == 102
        assert results[0]["location_status"] == "archived"

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_location_status_visible_only(self, mock_fetch_list, mock_fetch_details):
        """Test location_status filtering for visible ideas only"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101},
                {"id": 102},
                {"id": 103}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "hidden"},
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced(location_status="visible")

        assert len(results) == 2
        assert all(r["location_status"] == "visible" for r in results)

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_location_status_all(self, mock_fetch_list, mock_fetch_details):
        """Test location_status='all' includes all ideas"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101},
                {"id": 102},
                {"id": 103}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "archived"},
            {"id": 103, "location_status": "hidden"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced(location_status="all")

        # Should include all ideas regardless of status
        assert len(results) == 3

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_handles_missing_id(self, mock_fetch_list, mock_fetch_details):
        """Test that ideas without ID are included without detail fetch"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "name": "Idea 1"},
                {"name": "Idea without ID"},  # Missing ID
                {"id": 102, "name": "Idea 2"}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "visible"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced()

        # Should include all 3 ideas
        assert len(results) == 3
        # Should only call fetch_details twice (for ideas with IDs)
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_handles_fetch_details_error(self, mock_fetch_list, mock_fetch_details):
        """Test that errors fetching details don't break entire fetch"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101},
                {"id": 102},
                {"id": 103}
            ]
        }

        # Second detail fetch fails
        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            Exception("API Error"),
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource()
        results = resource.fetch_enhanced()

        # Should still return ideas 101 and 103 (102 failed but original data used)
        assert len(results) >= 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_with_filters(self, mock_fetch_list, mock_fetch_details):
        """Test that filters are passed to fetch_list"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource()
        filters = {"name": "Feature", "channel": "Sales"}
        resource.fetch_enhanced(filters=filters)

        # Verify filters were passed
        call_args = mock_fetch_list.call_args
        assert call_args[1]["filters"] == filters

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_get_all_pages(self, mock_fetch_list, mock_fetch_details):
        """Test that get_all parameter is passed through"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource()
        resource.fetch_enhanced(get_all=True)

        call_args = mock_fetch_list.call_args
        assert call_args[1]["get_all"] is True

    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_empty_results(self, mock_fetch_list):
        """Test handling of empty results"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource()
        results = resource.fetch_enhanced()

        assert results == []

    @patch.object(IdeasResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_missing_results_key(self, mock_fetch_list):
        """Test handling when API response missing 'results' key"""
        mock_fetch_list.return_value = {"paging": {}}

        resource = IdeasResource()
        results = resource.fetch_enhanced()

        assert results == []
