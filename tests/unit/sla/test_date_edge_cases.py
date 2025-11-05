#!/usr/bin/env python3
"""
Test edge cases for date formatting in Google Sheets storage

Run with: python -m pytest test_date_edge_cases.py -v
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from productplan_api_tools.sla.storage import GoogleSheetsSLAStorage


class TestDateEdgeCases(unittest.TestCase):
    """Test edge cases for date handling that might not be covered"""

    def setUp(self):
        self.credentials_file = '/fake/credentials.json'
        self.sheet_id = 'fake_sheet_id'
        self.sheet_name = 'Test Sheet'

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_handles_pandas_timestamp_correctly(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test that pandas Timestamps are converted to ISO strings"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with pandas Timestamp (common from API responses)
        df = pd.DataFrame({
            'id': [1],
            'created_at': [pd.Timestamp('2025-01-15 10:30:45')]
        })

        storage.write(df)

        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify pandas Timestamp is converted to string
        created_at = written_data[1][1]
        self.assertIsInstance(created_at, str)
        self.assertEqual(created_at, '2025-01-15 10:30:45')

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_handles_nat_as_empty_string(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test that NaT (Not a Time) values become empty strings"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with NaT value
        df = pd.DataFrame({
            'id': [1],
            'created_at': [pd.Timestamp('2025-01-15 10:30:45')],
            'response_sla': [pd.NaT]  # Not a Time - should become empty string
        })

        storage.write(df)

        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify NaT becomes empty string
        response_sla = written_data[1][2]
        self.assertEqual(response_sla, '')

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_strips_timezone_info(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test that timezone info is removed from datetime objects"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with timezone-aware datetime
        import pytz
        tz_aware_dt = datetime(2025, 1, 15, 10, 30, 45, tzinfo=pytz.UTC)
        df = pd.DataFrame({
            'id': [1],
            'created_at': [tz_aware_dt]
        })

        storage.write(df)

        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify timezone is stripped (no +00:00 or Z suffix)
        created_at = written_data[1][1]
        self.assertEqual(created_at, '2025-01-15 10:30:45')
        self.assertNotIn('+', created_at)
        self.assertNotIn('Z', created_at)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_handles_mixed_date_types(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test handling of mix of pandas Timestamps and Python datetimes"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with mixed date types
        df = pd.DataFrame({
            'id': [1, 2],
            'created_at': [
                pd.Timestamp('2025-01-15 10:30:45'),  # pandas Timestamp
                datetime(2025, 1, 20, 12, 0, 0)       # Python datetime
            ]
        })

        storage.write(df)

        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify both are converted to ISO strings
        row1_created = written_data[1][1]
        row2_created = written_data[2][1]
        self.assertEqual(row1_created, '2025-01-15 10:30:45')
        self.assertEqual(row2_created, '2025-01-20 12:00:00')


class TestRunsSheetHeaderValidation(unittest.TestCase):
    """Test Runs sheet header creation/validation logic"""

    def setUp(self):
        self.credentials_file = '/fake/credentials.json'
        self.sheet_id = 'fake_sheet_id'
        self.sheet_name = 'Test Sheet'

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    @patch('productplan_api_tools.sla.storage.config')
    def test_record_run_recreates_header_when_sheet_empty(
        self, mock_config, mock_exists, mock_creds, mock_gspread
    ):
        """Test that header is recreated if Runs sheet exists but is empty"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_runs_sheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        mock_config.get_runs_sheet_name.return_value = 'Runs'

        def worksheet_side_effect(name):
            if name == 'Runs':
                return mock_runs_sheet
            return mock_worksheet

        mock_spreadsheet.worksheet.side_effect = worksheet_side_effect

        # Mock empty sheet (no header)
        mock_runs_sheet.get_all_values.return_value = []

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        storage.record_run('init', records_added=5, records_updated=0)

        # Should call update() to write header + data (not append_row)
        mock_runs_sheet.update.assert_called_once()
        mock_runs_sheet.clear.assert_called_once()

        # Verify header + data written together
        update_call = mock_runs_sheet.update.call_args[0][0]
        self.assertEqual(len(update_call), 2)  # Header + data row
        self.assertEqual(update_call[0], ['type', 'timestamp', 'records_added', 'records_updated'])

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    @patch('productplan_api_tools.sla.storage.config')
    def test_record_run_recreates_header_when_wrong_header(
        self, mock_config, mock_exists, mock_creds, mock_gspread
    ):
        """Test that header is recreated if Runs sheet has wrong header"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_runs_sheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        mock_config.get_runs_sheet_name.return_value = 'Runs'

        def worksheet_side_effect(name):
            if name == 'Runs':
                return mock_runs_sheet
            return mock_worksheet

        mock_spreadsheet.worksheet.side_effect = worksheet_side_effect

        # Mock sheet with wrong/corrupted header
        mock_runs_sheet.get_all_values.return_value = [['old', 'wrong', 'header']]

        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        storage.record_run('init', records_added=5, records_updated=0)

        # Should call update() to recreate header + data
        mock_runs_sheet.update.assert_called_once()
        mock_runs_sheet.clear.assert_called_once()

        # Verify correct header written
        update_call = mock_runs_sheet.update.call_args[0][0]
        self.assertEqual(update_call[0], ['type', 'timestamp', 'records_added', 'records_updated'])


if __name__ == '__main__':
    unittest.main()
