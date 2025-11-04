"""
Unit tests for SLA manager functions

Tests filtering logic for excluding test/development ideas.
Tests URL generation for ProductPlan ideas.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch

from productplan_api_tools.sla.manager import apply_idea_filters, generate_idea_url


class TestApplyIdeaFilters:
    """Tests for apply_idea_filters() function"""

    def test_no_filtering_all_ideas_pass(self):
        """Test when all ideas pass filtering criteria"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Idea 1',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Alice',
                'customer': 'ACME Corp'
            },
            {
                'id': 2,
                'name': 'Idea 2',
                'created_at': '2025-10-01T12:00:00Z',
                'source_name': 'Bob',
                'customer': 'Beta Inc'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        assert len(filtered_df) == 2
        assert stats['date_filtered'] == 0
        assert stats['jason_filtered'] == 0
        assert stats['test_filtered'] == 0
        assert stats['total_filtered'] == 0
        assert stats['remaining'] == 2

    def test_date_cutoff_filter(self):
        """Test filtering by date cutoff (Sep 15, 2025)"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Old Idea',
                'created_at': '2025-09-14T12:00:00Z',  # Before cutoff
                'source_name': 'Alice',
                'customer': 'ACME'
            },
            {
                'id': 2,
                'name': 'New Idea',
                'created_at': '2025-09-15T12:00:00Z',  # On cutoff (should pass)
                'source_name': 'Bob',
                'customer': 'Beta'
            },
            {
                'id': 3,
                'name': 'Newer Idea',
                'created_at': '2025-09-16T12:00:00Z',  # After cutoff
                'source_name': 'Charlie',
                'customer': 'Gamma'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        assert len(filtered_df) == 2  # Ideas 2 and 3
        assert stats['date_filtered'] == 1
        assert list(filtered_df['id']) == [2, 3]

    def test_jason_ladicos_before_nov_3(self):
        """Test filtering Jason Ladicos ideas before Nov 3, 2025"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Jason Early Idea',
                'created_at': '2025-10-01T12:00:00Z',  # Before Nov 3
                'source_name': 'Jason Ladicos',
                'customer': 'ACME'
            },
            {
                'id': 2,
                'name': 'Jason Nov 3 Idea',
                'created_at': '2025-11-03T00:00:00Z',  # On Nov 3 (should pass)
                'source_name': 'Jason Ladicos',
                'customer': 'Beta'
            },
            {
                'id': 3,
                'name': 'Jason Late Idea',
                'created_at': '2025-11-04T12:00:00Z',  # After Nov 3
                'source_name': 'Jason Ladicos',
                'customer': 'Gamma'
            },
            {
                'id': 4,
                'name': 'Other Person Early',
                'created_at': '2025-10-01T12:00:00Z',  # Different person
                'source_name': 'Alice',
                'customer': 'Delta'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should keep ideas 2, 3, and 4 (filter out idea 1)
        assert len(filtered_df) == 3
        assert stats['jason_filtered'] == 1
        assert list(filtered_df['id']) == [2, 3, 4]

    def test_test_customer_filter(self):
        """Test filtering ideas with customer='TEST'"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Test Idea',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Alice',
                'customer': 'TEST'  # Exactly "TEST"
            },
            {
                'id': 2,
                'name': 'Test Lowercase',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Bob',
                'customer': 'test'  # Different case (should pass)
            },
            {
                'id': 3,
                'name': 'Real Customer',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Charlie',
                'customer': 'ACME Corp'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should keep ideas 2 and 3 (filter out idea 1)
        assert len(filtered_df) == 2
        assert stats['test_filtered'] == 1
        assert list(filtered_df['id']) == [2, 3]

    def test_multiple_filters_applied(self):
        """Test that all filters are applied together"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Too Old',
                'created_at': '2025-09-01T12:00:00Z',  # Fails date filter
                'source_name': 'Alice',
                'customer': 'ACME'
            },
            {
                'id': 2,
                'name': 'Jason Early',
                'created_at': '2025-10-01T12:00:00Z',  # Fails Jason filter
                'source_name': 'Jason Ladicos',
                'customer': 'Beta'
            },
            {
                'id': 3,
                'name': 'Test Customer',
                'created_at': '2025-09-16T12:00:00Z',  # Fails TEST filter
                'source_name': 'Bob',
                'customer': 'TEST'
            },
            {
                'id': 4,
                'name': 'Good Idea',
                'created_at': '2025-09-16T12:00:00Z',  # Passes all filters
                'source_name': 'Charlie',
                'customer': 'Gamma'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should only keep idea 4
        assert len(filtered_df) == 1
        assert stats['date_filtered'] == 1
        assert stats['jason_filtered'] == 1
        assert stats['test_filtered'] == 1
        assert stats['total_filtered'] == 3
        assert stats['remaining'] == 1
        assert list(filtered_df['id']) == [4]

    def test_empty_dataframe(self):
        """Test filtering an empty DataFrame"""
        df = pd.DataFrame(columns=['id', 'name', 'created_at', 'source_name', 'customer'])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        assert len(filtered_df) == 0
        assert stats['total_filtered'] == 0
        assert stats['remaining'] == 0

    def test_null_values_handling(self):
        """Test filtering with null values in source_name and customer"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Null Customer',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Alice',
                'customer': None  # Null customer (not "TEST", should pass)
            },
            {
                'id': 2,
                'name': 'Null Source',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': None,  # Null source (not Jason, should pass)
                'customer': 'ACME'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Both should pass all filters
        assert len(filtered_df) == 2
        assert stats['jason_filtered'] == 0
        assert stats['test_filtered'] == 0

    def test_exact_boundary_dates(self):
        """Test exact boundary dates for Sep 15 and Nov 3"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Sep 14 23:59:59',
                'created_at': '2025-09-14T23:59:59Z',  # Just before Sep 15
                'source_name': 'Alice',
                'customer': 'ACME'
            },
            {
                'id': 2,
                'name': 'Sep 15 00:00:00',
                'created_at': '2025-09-15T00:00:00Z',  # Exactly Sep 15
                'source_name': 'Bob',
                'customer': 'Beta'
            },
            {
                'id': 3,
                'name': 'Jason Nov 2 23:59:59',
                'created_at': '2025-11-02T23:59:59Z',  # Just before Nov 3
                'source_name': 'Jason Ladicos',
                'customer': 'Gamma'
            },
            {
                'id': 4,
                'name': 'Jason Nov 3 00:00:00',
                'created_at': '2025-11-03T00:00:00Z',  # Exactly Nov 3
                'source_name': 'Jason Ladicos',
                'customer': 'Delta'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should keep 2 and 4 (filter out 1 and 3)
        assert len(filtered_df) == 2
        assert stats['date_filtered'] == 1
        assert stats['jason_filtered'] == 1
        assert list(filtered_df['id']) == [2, 4]

    def test_whitespace_in_test_customer(self):
        """Test that 'TEST ' with trailing space is NOT filtered (exact match only)"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Exact TEST',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Alice',
                'customer': 'TEST'  # Exact match - should be filtered
            },
            {
                'id': 2,
                'name': 'TEST with trailing space',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Bob',
                'customer': 'TEST '  # With space - should NOT be filtered (not exact match)
            },
            {
                'id': 3,
                'name': 'TEST with leading space',
                'created_at': '2025-09-16T12:00:00Z',
                'source_name': 'Charlie',
                'customer': ' TEST'  # With space - should NOT be filtered
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should keep 2 and 3 (only filter out exact match)
        assert len(filtered_df) == 2
        assert stats['test_filtered'] == 1  # Only exact "TEST" filtered
        assert list(filtered_df['id']) == [2, 3]

    def test_case_variations_in_jason_ladicos(self):
        """Test that Jason Ladicos filter is case-sensitive (exact match)"""
        df = pd.DataFrame([
            {
                'id': 1,
                'name': 'Exact Match',
                'created_at': '2025-10-01T12:00:00Z',
                'source_name': 'Jason Ladicos',  # Exact - should be filtered
                'customer': 'ACME'
            },
            {
                'id': 2,
                'name': 'Lowercase jason',
                'created_at': '2025-10-01T12:00:00Z',
                'source_name': 'jason ladicos',  # Different case - should NOT be filtered
                'customer': 'Beta'
            },
            {
                'id': 3,
                'name': 'All caps',
                'created_at': '2025-10-01T12:00:00Z',
                'source_name': 'JASON LADICOS',  # Different case - should NOT be filtered
                'customer': 'Gamma'
            },
            {
                'id': 4,
                'name': 'Jason on Nov 3',
                'created_at': '2025-11-03T00:00:00Z',  # On Nov 3 boundary
                'source_name': 'Jason Ladicos',
                'customer': 'Delta'
            }
        ])

        filtered_df, stats = apply_idea_filters(df, verbose=False)

        # Should keep 2, 3, and 4 (only filter out 1)
        # Note: 4 passes because it's ON Nov 3 (not before)
        assert len(filtered_df) == 3
        assert stats['jason_filtered'] == 1  # Only exact match before Nov 3
        assert list(filtered_df['id']) == [2, 3, 4]


class TestGenerateIdeaUrl:
    """Tests for generate_idea_url() function"""

    @patch('productplan_api_tools.sla.manager.config')
    def test_basic_url_generation(self, mock_config):
        """Test basic URL generation with clean prefix"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

        url = generate_idea_url(12345)

        assert url == 'https://app.productplan.com/ideas/12345'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_trailing_slash(self, mock_config):
        """Test URL generation strips trailing slash from prefix"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas/'

        url = generate_idea_url(12345)

        # Should strip trailing slash to avoid double slash
        assert url == 'https://app.productplan.com/ideas/12345'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_multiple_trailing_slashes(self, mock_config):
        """Test URL generation strips multiple trailing slashes"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas///'

        url = generate_idea_url(67890)

        # Should strip all trailing slashes
        assert url == 'https://app.productplan.com/ideas/67890'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_different_prefix(self, mock_config):
        """Test URL generation works with different URL prefixes"""
        mock_config.get_url_prefix.return_value = 'https://custom.domain.com/portal/ideas'

        url = generate_idea_url(99999)

        assert url == 'https://custom.domain.com/portal/ideas/99999'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_small_id(self, mock_config):
        """Test URL generation with single digit ID"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

        url = generate_idea_url(1)

        assert url == 'https://app.productplan.com/ideas/1'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_large_id(self, mock_config):
        """Test URL generation with large ID"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

        url = generate_idea_url(999999999)

        assert url == 'https://app.productplan.com/ideas/999999999'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_zero_id(self, mock_config):
        """Test URL generation with ID = 0 (valid edge case)"""
        mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

        url = generate_idea_url(0)

        assert url == 'https://app.productplan.com/ideas/0'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_empty_prefix(self, mock_config):
        """Test URL generation with empty string prefix"""
        mock_config.get_url_prefix.return_value = ''

        url = generate_idea_url(12345)

        # Empty prefix gets stripped, results in just "/12345"
        assert url == '/12345'

    @patch('productplan_api_tools.sla.manager.config')
    def test_url_generation_with_only_slashes_prefix(self, mock_config):
        """Test URL generation with prefix containing only slashes"""
        mock_config.get_url_prefix.return_value = '///'

        url = generate_idea_url(12345)

        # All slashes get stripped, results in just "/12345"
        assert url == '/12345'
