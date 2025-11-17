"""
Unit tests for IdeasResource class

Tests ideas endpoint with enhanced detail fetching and location filtering.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.ideas import IdeasResource


class TestIdeasResourceEndpoint:
    """Test IdeasResource endpoint configuration"""

    def test_endpoint_path(self):
        """Test that endpoint_path is correctly set"""
        resource = IdeasResource(token="test_token")
        assert resource.endpoint_path == "discovery/ideas"


class TestIdeasResourceFetchEnhanced:
    """Test IdeasResource.fetch_enhanced() method"""

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(page=1, page_size=100, get_all=False)

        assert len(results) == 2
        assert results[0]["created_at"] == "2024-01-01"
        assert results[1]["created_at"] == "2024-01-02"

        # Should fetch details for each idea
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(location_status="not_archived")

        # Should exclude archived idea (102)
        assert len(results) == 2
        assert all(r["location_status"] != "archived" for r in results)

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(location_status="archived")

        # Should only include archived idea
        assert len(results) == 1
        assert results[0]["id"] == 102
        assert results[0]["location_status"] == "archived"

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(location_status="visible")

        assert len(results) == 2
        assert all(r["location_status"] == "visible" for r in results)

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(location_status="all")

        # Should include all ideas regardless of status
        assert len(results) == 3

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should include all 3 ideas
        assert len(results) == 3
        # Should only call fetch_details twice (for ideas with IDs)
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
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

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should still return ideas 101 and 103 (102 failed but original data used)
        assert len(results) >= 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_with_filters(self, mock_fetch_list, mock_fetch_details):
        """Test that filters are passed to fetch_list"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource(token="test_token")
        filters = {"name": "Feature", "channel": "Sales"}
        resource.fetch_enhanced(filters=filters)

        # Verify filters were passed
        call_args = mock_fetch_list.call_args
        assert call_args[1]["filters"] == filters

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_get_all_pages(self, mock_fetch_list, mock_fetch_details):
        """Test that get_all parameter is passed through"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource(token="test_token")
        resource.fetch_enhanced(get_all=True)

        call_args = mock_fetch_list.call_args
        assert call_args[1]["get_all"] is True

    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_empty_results(self, mock_fetch_list):
        """Test handling of empty results"""
        mock_fetch_list.return_value = {"results": []}

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        assert results == []

    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_missing_results_key(self, mock_fetch_list):
        """Test handling when API response missing 'results' key"""
        mock_fetch_list.return_value = {"paging": {}}

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        assert results == []

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_excludes_ignore_status_by_default(self, mock_fetch_list, mock_fetch_details):
        """Test that ideas with 'Ignore' status are excluded by default"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "idea status", "value": "On deck"}]},
                {"id": 102, "custom_dropdown_fields": [{"label": "idea status", "value": "Ignore"}]},
                {"id": 103, "custom_dropdown_fields": [{"label": "idea status", "value": "Accepted"}]}
            ]
        }

        # Should only fetch details for non-Ignore ideas (101 and 103)
        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should exclude idea 102 with "Ignore" status
        assert len(results) == 2
        assert results[0]["id"] == 101
        assert results[1]["id"] == 103
        # Should only call fetch_details twice (not for "Ignore" idea)
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_includes_ignore_status_when_all(self, mock_fetch_list, mock_fetch_details):
        """Test that ideas with 'Ignore' status are included when idea_status='all'"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "idea status", "value": "On deck"}]},
                {"id": 102, "custom_dropdown_fields": [{"label": "idea status", "value": "Ignore"}]},
                {"id": 103, "custom_dropdown_fields": [{"label": "idea status", "value": "Accepted"}]}
            ]
        }

        # Should fetch details ONLY for non-Ignore ideas (optimization)
        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(idea_status="all")

        # Should include all 3 ideas
        assert len(results) == 3
        assert results[0]["id"] == 101
        assert results[1]["id"] == 102
        assert results[2]["id"] == 103
        # Should call fetch_details only 2 times (skips "Ignore" idea for efficiency)
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_excludes_ignore_case_insensitive(self, mock_fetch_list, mock_fetch_details):
        """Test that 'idea status' field matching is case-insensitive"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "Idea Status", "value": "Ignore"}]},
                {"id": 102, "custom_dropdown_fields": [{"label": "IDEA STATUS", "value": "Ignore"}]},
                {"id": 103, "custom_dropdown_fields": [{"label": "idea status", "value": "Accepted"}]}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should exclude ideas 101 and 102 (case-insensitive field matching)
        assert len(results) == 1
        assert results[0]["id"] == 103
        assert mock_fetch_details.call_count == 1

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_handles_missing_custom_dropdown_fields(self, mock_fetch_list, mock_fetch_details):
        """Test that ideas without custom_dropdown_fields are not filtered out"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "idea status", "value": "On deck"}]},
                {"id": 102},  # Missing custom_dropdown_fields
                {"id": 103, "custom_dropdown_fields": None}  # None value
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "visible"},
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should include all ideas (missing fields don't have "Ignore" status)
        assert len(results) == 3
        assert mock_fetch_details.call_count == 3

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_idea_status_combined_with_location_status(self, mock_fetch_list, mock_fetch_details):
        """Test that idea_status and location_status filters work together"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "idea status", "value": "On deck"}]},
                {"id": 102, "custom_dropdown_fields": [{"label": "idea status", "value": "Ignore"}]},
                {"id": 103, "custom_dropdown_fields": [{"label": "idea status", "value": "Accepted"}]}
            ]
        }

        # Mix of location statuses
        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "archived"},  # Filtered by location_status
            {"id": 103, "location_status": "visible"}     # Passes both filters
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced(location_status="not_archived")

        # Should exclude 102 (Ignore status) and 101 (archived)
        assert len(results) == 1
        assert results[0]["id"] == 103
        # Should fetch details for 101 and 103 (102 skipped due to Ignore status)
        assert mock_fetch_details.call_count == 2

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_handles_none_value_in_status_field(self, mock_fetch_list, mock_fetch_details):
        """Test that ideas with None value in status field are not filtered out"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [{"label": "idea status", "value": None}]},
                {"id": 102, "custom_dropdown_fields": [{"label": "idea status", "value": ""}]},
                {"id": 103, "custom_dropdown_fields": [{"label": "idea status", "value": "On deck"}]}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"},
            {"id": 102, "location_status": "visible"},
            {"id": 103, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # All ideas should be included (None and empty string are not "Ignore")
        assert len(results) == 3
        assert mock_fetch_details.call_count == 3

    @patch.object(IdeasResource, 'fetch_details')
    @patch.object(IdeasResource, 'fetch_list')
    def test_fetch_enhanced_multiple_dropdown_fields(self, mock_fetch_list, mock_fetch_details):
        """Test that only the 'idea status' field is used for filtering"""
        mock_fetch_list.return_value = {
            "results": [
                {"id": 101, "custom_dropdown_fields": [
                    {"label": "priority", "value": "Ignore"},  # Different field
                    {"label": "idea status", "value": "On deck"}
                ]},
                {"id": 102, "custom_dropdown_fields": [
                    {"label": "idea status", "value": "Ignore"},
                    {"label": "priority", "value": "High"}
                ]}
            ]
        }

        mock_fetch_details.side_effect = [
            {"id": 101, "location_status": "visible"}
        ]

        resource = IdeasResource(token="test_token")
        results = resource.fetch_enhanced()

        # Should only look at "idea status" field, not "priority"
        assert len(results) == 1
        assert results[0]["id"] == 101
        assert mock_fetch_details.call_count == 1
