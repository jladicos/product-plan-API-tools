"""
Unit tests for IdeaFormsResource class

Tests idea forms endpoint with enhanced detail fetching.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.idea_forms import IdeaFormsResource


class TestIdeaFormsResourceEndpoint:
    """Test IdeaFormsResource endpoint configuration"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set"""
        resource = IdeaFormsResource()
        assert resource.endpoint_path == "discovery/idea_forms"


class TestIdeaFormsResourceFetchEnhanced:
    """Test IdeaFormsResource.fetch_enhanced() method"""

    @patch.object(IdeaFormsResource, 'fetch_details')
    @patch.object(IdeaFormsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_basic(self, mock_fetch_list, mock_fetch_details):
        """Test basic enhanced fetching with detail calls"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "title": "Form 1"},
                {"id": 2, "title": "Form 2"}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 1, "title": "Form 1", "instructions": "Fill this out", "custom_text_fields": []},
            {"id": 2, "title": "Form 2", "instructions": "Another form", "custom_dropdown_fields": []}
        ]

        resource = IdeaFormsResource()
        results = resource.fetch_enhanced()

        assert len(results) == 2
        assert results[0]["instructions"] == "Fill this out"
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeaFormsResource, 'fetch_details')
    @patch.object(IdeaFormsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_handles_missing_id(self, mock_fetch_list, mock_fetch_details):
        """Test that forms without ID are included without detail fetch"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1, "title": "Form 1"},
                {"title": "Form without ID"},
                {"id": 2, "title": "Form 2"}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 1, "custom_fields": []},
            {"id": 2, "custom_fields": []}
        ]

        resource = IdeaFormsResource()
        results = resource.fetch_enhanced()

        assert len(results) == 3
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeaFormsResource, 'fetch_details')
    @patch.object(IdeaFormsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_handles_fetch_error(self, mock_fetch_list, mock_fetch_details):
        """Test that errors fetching details are handled gracefully"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 1},
                {"id": 2}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 1, "data": "success"},
            Exception("API Error")
        ]

        resource = IdeaFormsResource()
        results = resource.fetch_enhanced()

        # Should include both forms (second one with original data)
        assert len(results) == 2

    @patch.object(IdeaFormsResource, 'fetch_list')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_enhanced_empty_results(self, mock_fetch_list):
        """Test handling of empty results"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeaFormsResource()
        results = resource.fetch_enhanced()

        assert results == []
