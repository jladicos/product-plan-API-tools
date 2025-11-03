"""
Unit tests for SLA calculator functions

Tests pure business logic without I/O dependencies.
"""

import pytest
from datetime import datetime, timedelta
from productplan_api_tools.sla.calculator import (
    extract_idea_status,
    calculate_sla_columns,
    compare_timestamps
)


class TestExtractIdeaStatus:
    """Tests for extract_idea_status() function"""

    def test_valid_idea_status_field(self):
        """Test extracting idea status from valid custom dropdown field"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ]
        }
        assert extract_idea_status(idea) == 'Accepted'

    def test_missing_custom_dropdown_fields(self):
        """Test handling of missing custom_dropdown_fields key"""
        idea = {}
        assert extract_idea_status(idea) == ''

    def test_empty_custom_dropdown_fields(self):
        """Test handling of empty custom_dropdown_fields list"""
        idea = {'custom_dropdown_fields': []}
        assert extract_idea_status(idea) == ''

    def test_different_status_values(self):
        """Test extracting different status values"""
        statuses = ['On deck', 'Accepted', 'Rejected', 'In Review']
        for status in statuses:
            idea = {
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': status}
                ]
            }
            assert extract_idea_status(idea) == status

    def test_idea_status_not_present(self):
        """Test when idea status field is not in custom dropdowns"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'priority', 'value': 'High'},
                {'label': 'category', 'value': 'Feature'}
            ]
        }
        assert extract_idea_status(idea) == ''

    def test_case_sensitivity(self):
        """Test that label matching is case-insensitive"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'Idea Status', 'value': 'Accepted'}  # Capital I and S
            ]
        }
        # Label matching should be case-insensitive to handle variations
        result = extract_idea_status(idea)
        # Should match "Idea Status" even though we're looking for "idea status"
        assert result == 'Accepted'

    def test_explicit_none_value(self):
        """Test handling when value is explicitly None (not missing)"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': None}  # Explicitly None
            ]
        }
        result = extract_idea_status(idea)
        # Should return empty string, not None
        assert result == ''
        assert isinstance(result, str)

    def test_duplicate_idea_status_fields(self):
        """Test handling when multiple 'idea status' fields exist"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'On deck'},
                {'label': 'idea status', 'value': 'Accepted'},  # Duplicate
            ]
        }
        result = extract_idea_status(idea)
        # Should return first match
        assert result == 'On deck'


class TestCalculateSLAColumns:
    """Tests for calculate_sla_columns() function"""

    def test_new_idea_on_deck_status(self):
        """Test new idea with 'On deck' status - no SLA dates set"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'On deck'}
            ],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        result = calculate_sla_columns(idea)

        assert result['response_sla'] is None
        assert result['roadmap_sla'] is None
        assert result['currently_meets_response_sla'] is False
        assert result['currently_meets_roadmap_sla'] is False

    def test_new_idea_in_review_within_14_days(self):
        """Test idea with 'In Review' status changed within 14 days - meets response SLA"""
        # Created on Jan 1, changed to In Review on Jan 10 (9 days later)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 1, 10, 12, 0, 0)  # Status changed on this date
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # response_sla should be set to updated_at (when status was changed)
        assert result['response_sla'] is not None
        assert isinstance(result['response_sla'], datetime)
        assert result['response_sla'] == updated_at.replace(tzinfo=result['response_sla'].tzinfo)

        assert result['roadmap_sla'] is None
        assert result['currently_meets_response_sla'] is True  # Within 14 days
        assert result['currently_meets_roadmap_sla'] is False

    def test_new_idea_in_review_after_14_days(self):
        """Test idea with 'In Review' status changed after 14 days - fails response SLA"""
        # Created on Jan 1, changed to In Review on Feb 10 (40 days later - late response)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 2, 10, 12, 0, 0)  # 40 days after creation
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # response_sla should be set to updated_at but boolean should be False (late)
        assert result['response_sla'] is not None
        assert result['response_sla'] == updated_at.replace(tzinfo=result['response_sla'].tzinfo)
        assert result['roadmap_sla'] is None
        assert result['currently_meets_response_sla'] is False  # More than 14 days
        assert result['currently_meets_roadmap_sla'] is False

    def test_accepted_within_both_slas(self):
        """Test 'Accepted' status within both 14 and 60 day windows - meets both SLAs"""
        # Created on Jan 1, accepted on Jan 10 (9 days later)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 1, 10, 12, 0, 0)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # Both SLA dates should be set to updated_at
        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert result['response_sla'] == updated_at.replace(tzinfo=result['response_sla'].tzinfo)
        assert result['roadmap_sla'] == updated_at.replace(tzinfo=result['roadmap_sla'].tzinfo)
        # Both booleans should be True (within windows)
        assert result['currently_meets_response_sla'] is True
        assert result['currently_meets_roadmap_sla'] is True

    def test_accepted_after_14_within_60(self):
        """Test 'Accepted' after 14 days but within 60 - fails response, meets roadmap"""
        # Created on Jan 1, accepted on Feb 10 (40 days later)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 2, 10, 12, 0, 0)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert result['currently_meets_response_sla'] is False  # More than 14 days
        assert result['currently_meets_roadmap_sla'] is True   # Within 60 days

    def test_accepted_after_60_days(self):
        """Test 'Accepted' after 60 days - fails both SLAs"""
        # Created on Jan 1, accepted on Apr 15 (105 days later)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 4, 15, 12, 0, 0)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert result['currently_meets_response_sla'] is False  # More than 14 days
        assert result['currently_meets_roadmap_sla'] is False   # More than 60 days

    def test_preserve_existing_response_sla(self):
        """Test that existing response_sla date is preserved"""
        # Created Jan 1, response SLA set Jan 6, now updated to Accepted on Jan 15
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        existing_response_date = datetime(2024, 1, 6, 12, 0, 0)  # 5 days after creation
        updated_at = datetime(2024, 1, 15, 12, 0, 0)  # Now accepted

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }
        existing_sla_data = {
            'response_sla': existing_response_date,
            'roadmap_sla': None
        }

        result = calculate_sla_columns(idea, existing_sla_data)

        # Should preserve the existing response_sla date
        assert result['response_sla'] == existing_response_date
        # roadmap_sla should be set to updated_at (Jan 15)
        assert result['roadmap_sla'] is not None
        assert result['roadmap_sla'] == updated_at.replace(tzinfo=result['roadmap_sla'].tzinfo)
        # response_sla is 5 days after creation (within 14 days)
        assert result['currently_meets_response_sla'] is True
        # roadmap_sla is 14 days after creation (within 60 days)
        assert result['currently_meets_roadmap_sla'] is True

    def test_status_regression_accepted_to_on_deck(self):
        """Test status regression: Accepted → On deck (preserve dates, update booleans)"""
        # Dates are preserved but status regressed, so booleans are False
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 3, 1, 12, 0, 0)  # Regressed back on Mar 1
        existing_response_date = datetime(2024, 1, 10, 12, 0, 0)
        existing_roadmap_date = datetime(2024, 2, 15, 12, 0, 0)

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'On deck'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }
        existing_sla_data = {
            'response_sla': existing_response_date,
            'roadmap_sla': existing_roadmap_date
        }

        result = calculate_sla_columns(idea, existing_sla_data)

        # Historical dates preserved
        assert result['response_sla'] == existing_response_date
        assert result['roadmap_sla'] == existing_roadmap_date
        # Current state booleans are False (status is "On deck", not valid)
        assert result['currently_meets_response_sla'] is False
        assert result['currently_meets_roadmap_sla'] is False

    def test_multiple_transitions(self):
        """Test multiple status transitions: On deck → In Review → Accepted"""
        # Created Jan 1, first update Jan 5, second update Jan 10
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        first_update = datetime(2024, 1, 5, 12, 0, 0)
        second_update = datetime(2024, 1, 10, 12, 0, 0)

        # First transition: On deck → In Review (Jan 5)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': first_update.isoformat() + 'Z'
        }
        result1 = calculate_sla_columns(idea)
        response_sla_date = result1['response_sla']

        assert response_sla_date is not None
        assert response_sla_date == first_update.replace(tzinfo=response_sla_date.tzinfo)
        assert result1['roadmap_sla'] is None
        assert result1['currently_meets_response_sla'] is True  # Within 14 days

        # Second transition: In Review → Accepted (Jan 10)
        idea['custom_dropdown_fields'][0]['value'] = 'Accepted'
        idea['updated_at'] = second_update.isoformat() + 'Z'
        existing_sla_data = {
            'response_sla': response_sla_date,
            'roadmap_sla': None
        }
        result2 = calculate_sla_columns(idea, existing_sla_data)

        # response_sla unchanged, roadmap_sla newly set to second_update
        assert result2['response_sla'] == response_sla_date
        assert result2['roadmap_sla'] is not None
        assert result2['roadmap_sla'] == second_update.replace(tzinfo=result2['roadmap_sla'].tzinfo)
        assert result2['currently_meets_response_sla'] is True  # Still within 14 days
        assert result2['currently_meets_roadmap_sla'] is True  # Within 60 days

    def test_missing_idea_status(self):
        """Test graceful handling of missing/null idea status"""
        idea = {
            'custom_dropdown_fields': [],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        result = calculate_sla_columns(idea)

        # Should handle gracefully, treating as "On deck" or no status
        assert result['response_sla'] is None
        assert result['roadmap_sla'] is None
        assert result['currently_meets_response_sla'] is False
        assert result['currently_meets_roadmap_sla'] is False

    def test_rejected_status(self):
        """Test 'Rejected' status sets roadmap_sla (within both SLAs)"""
        # Created Jan 1, rejected Jan 10 (9 days later)
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 1, 10, 12, 0, 0)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Rejected'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }
        result = calculate_sla_columns(idea)

        # Both SLAs should be set to updated_at for Rejected status
        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert result['response_sla'] == updated_at.replace(tzinfo=result['response_sla'].tzinfo)
        assert result['roadmap_sla'] == updated_at.replace(tzinfo=result['roadmap_sla'].tzinfo)
        # Rejected within 14 days (response) and 60 days (roadmap)
        assert result['currently_meets_response_sla'] is True
        assert result['currently_meets_roadmap_sla'] is True

    def test_empty_status_value(self):
        """Test idea with empty status value (not null, but empty string)"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': ''}
            ],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        result = calculate_sla_columns(idea)

        # Empty status treated like no status
        assert result['response_sla'] is None
        assert result['roadmap_sla'] is None
        assert result['currently_meets_response_sla'] is False
        assert result['currently_meets_roadmap_sla'] is False

    def test_missing_updated_at_falls_back_to_now(self):
        """Test that SLA date uses current time when updated_at is missing"""
        created_at = datetime(2024, 1, 1, 0, 0, 0)
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z'
            # No updated_at provided - should fall back to current time
        }

        # Capture time window
        before = datetime.utcnow()
        result = calculate_sla_columns(idea)
        after = datetime.utcnow()

        # response_sla should fall back to "now" (within test execution window)
        assert result['response_sla'] is not None
        assert isinstance(result['response_sla'], datetime)
        assert before <= result['response_sla'] <= after

        # Should NOT meet SLA because response is way after creation
        assert result['currently_meets_response_sla'] is False

    def test_response_sla_exactly_14_days(self):
        """Test boundary condition: response exactly 14 days after creation"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 15, 12, 0, 0)  # Exactly 14 days later

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # Exactly 14 days should MEET the SLA (≤ 14 days)
        assert result['response_sla'] is not None
        days_diff = (result['response_sla'] - created_at.replace(tzinfo=result['response_sla'].tzinfo)).days
        assert days_diff == 14
        assert result['currently_meets_response_sla'] is True

    def test_response_sla_just_over_14_days(self):
        """Test boundary condition: response just over 14 days fails SLA"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 16, 12, 0, 1)  # 15 days and 1 second later

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # Over 14 days should FAIL the SLA
        assert result['response_sla'] is not None
        days_diff = (result['response_sla'] - created_at.replace(tzinfo=result['response_sla'].tzinfo)).days
        assert days_diff > 14
        assert result['currently_meets_response_sla'] is False

    def test_roadmap_sla_exactly_60_days(self):
        """Test boundary condition: decision exactly 60 days after creation"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 3, 1, 12, 0, 0)  # Exactly 60 days later

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # Exactly 60 days should MEET the SLA (≤ 60 days)
        assert result['roadmap_sla'] is not None
        days_diff = (result['roadmap_sla'] - created_at.replace(tzinfo=result['roadmap_sla'].tzinfo)).days
        assert days_diff == 60
        assert result['currently_meets_roadmap_sla'] is True

    def test_roadmap_sla_just_over_60_days(self):
        """Test boundary condition: decision just over 60 days fails SLA"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 3, 2, 12, 0, 1)  # 61 days and 1 second later

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        result = calculate_sla_columns(idea)

        # Over 60 days should FAIL the SLA
        assert result['roadmap_sla'] is not None
        days_diff = (result['roadmap_sla'] - created_at.replace(tzinfo=result['roadmap_sla'].tzinfo)).days
        assert days_diff > 60
        assert result['currently_meets_roadmap_sla'] is False

    def test_pandas_timestamp_in_calculate_sla_columns(self):
        """Test that pandas Timestamp objects work (not just strings)"""
        import pandas as pd

        created_at = pd.Timestamp('2024-01-01 10:00:00')
        updated_at = pd.Timestamp('2024-01-10 12:00:00')

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at,  # Pandas Timestamp object
            'updated_at': updated_at   # Pandas Timestamp object
        }

        result = calculate_sla_columns(idea)

        # Should handle pandas Timestamps correctly
        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert isinstance(result['response_sla'], datetime)
        assert isinstance(result['roadmap_sla'], datetime)
        assert result['currently_meets_response_sla'] is True
        assert result['currently_meets_roadmap_sla'] is True

    def test_existing_sla_with_nat_value(self):
        """Test that pd.NaT in existing_sla_data is treated as None"""
        import pandas as pd

        created_at = datetime(2024, 1, 1, 0, 0, 0)
        updated_at = datetime(2024, 1, 10, 12, 0, 0)

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'created_at': created_at.isoformat() + 'Z',
            'updated_at': updated_at.isoformat() + 'Z'
        }

        existing_sla_data = {
            'response_sla': pd.NaT,  # Not a Time (pandas null for datetime)
            'roadmap_sla': pd.NaT
        }

        result = calculate_sla_columns(idea, existing_sla_data)

        # NaT should be treated as "not set", so new dates should be set
        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None
        assert isinstance(result['response_sla'], datetime)
        assert isinstance(result['roadmap_sla'], datetime)

    def test_missing_created_at(self):
        """Test graceful handling when created_at is missing"""
        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            # No created_at provided - should handle gracefully
            'updated_at': '2024-01-10T12:00:00Z'
        }

        # Should not crash - handle gracefully
        result = calculate_sla_columns(idea)

        # SLA dates should still be set (from updated_at)
        assert result['response_sla'] is not None
        assert result['roadmap_sla'] is not None

        # Booleans should be False (can't calculate compliance without created_at)
        assert result['currently_meets_response_sla'] is False
        assert result['currently_meets_roadmap_sla'] is False

    def test_timezone_aware_datetime_mixing(self):
        """Test mixing timezone-aware and naive datetime objects"""
        from datetime import timezone

        # Timezone-aware datetime
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        # Naive datetime
        updated_at = datetime(2024, 1, 10, 12, 0, 0)

        idea = {
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'created_at': created_at.isoformat(),
            'updated_at': updated_at.isoformat() + 'Z'
        }

        # Should handle mixed timezone awareness
        result = calculate_sla_columns(idea)

        assert result['response_sla'] is not None
        assert result['currently_meets_response_sla'] is True


class TestCompareTimestamps:
    """Tests for compare_timestamps() function"""

    def test_api_newer_than_spreadsheet(self):
        """Test when API timestamp is newer"""
        api_ts = '2024-01-15T10:00:00Z'
        sheet_ts = '2024-01-14T10:00:00Z'
        assert compare_timestamps(api_ts, sheet_ts) is True

    def test_api_older_than_spreadsheet(self):
        """Test when API timestamp is older"""
        api_ts = '2024-01-14T10:00:00Z'
        sheet_ts = '2024-01-15T10:00:00Z'
        assert compare_timestamps(api_ts, sheet_ts) is False

    def test_equal_timestamps(self):
        """Test when timestamps are equal"""
        ts = '2024-01-15T10:00:00Z'
        assert compare_timestamps(ts, ts) is False

    def test_missing_api_timestamp(self):
        """Test graceful handling of missing API timestamp"""
        sheet_ts = '2024-01-15T10:00:00Z'
        # Should handle None or empty string
        assert compare_timestamps(None, sheet_ts) is False
        assert compare_timestamps('', sheet_ts) is False

    def test_missing_spreadsheet_timestamp(self):
        """Test graceful handling of missing spreadsheet timestamp"""
        api_ts = '2024-01-15T10:00:00Z'
        # Should handle None or empty string
        # When spreadsheet has no timestamp, API should be considered newer
        assert compare_timestamps(api_ts, None) is True
        assert compare_timestamps(api_ts, '') is True

    def test_invalid_timestamp_format(self):
        """Test graceful handling of invalid timestamp format"""
        api_ts = 'not-a-timestamp'
        sheet_ts = '2024-01-15T10:00:00Z'
        # Should handle gracefully and return False
        assert compare_timestamps(api_ts, sheet_ts) is False

    def test_different_timestamp_formats(self):
        """Test handling of different valid ISO format variations"""
        # With milliseconds
        api_ts = '2024-01-15T10:00:00.123Z'
        sheet_ts = '2024-01-15T09:00:00Z'
        assert compare_timestamps(api_ts, sheet_ts) is True

        # Without Z (timezone) - should still parse and compare correctly
        api_ts = '2024-01-15T10:00:00'
        sheet_ts = '2024-01-15T09:00:00'
        assert compare_timestamps(api_ts, sheet_ts) is True  # 10:00 > 09:00

        # Reverse: earlier time should return False
        api_ts = '2024-01-15T08:00:00'
        sheet_ts = '2024-01-15T09:00:00'
        assert compare_timestamps(api_ts, sheet_ts) is False  # 08:00 < 09:00

    def test_pandas_timestamp_in_compare_timestamps(self):
        """Test that pandas Timestamp objects work in compare_timestamps"""
        import pandas as pd

        # API returns pandas Timestamp (newer)
        api_ts = pd.Timestamp('2024-01-15 10:00:00')
        sheet_ts = '2024-01-15T09:00:00Z'
        assert compare_timestamps(api_ts, sheet_ts) is True

        # Spreadsheet has pandas Timestamp (newer)
        api_ts = '2024-01-15T08:00:00Z'
        sheet_ts = pd.Timestamp('2024-01-15 09:00:00')
        assert compare_timestamps(api_ts, sheet_ts) is False

        # Both are pandas Timestamps
        api_ts = pd.Timestamp('2024-01-15 10:00:00')
        sheet_ts = pd.Timestamp('2024-01-15 09:00:00')
        assert compare_timestamps(api_ts, sheet_ts) is True
