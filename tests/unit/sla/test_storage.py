"""
Unit tests for SLA storage implementations
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
import os
from datetime import datetime
import tempfile

from productplan_api_tools.sla.storage import (
    ExcelSLAStorage,
    GoogleSheetsSLAStorage
)


class TestExcelSLAStorage(unittest.TestCase):
    """Tests for Excel storage implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test_sla.xlsx')

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_exists_returns_true_when_file_exists(self):
        """Test exists() returns True when file exists"""
        storage = ExcelSLAStorage(self.test_file)

        # Create empty file
        with open(self.test_file, 'w') as f:
            f.write('')

        self.assertTrue(storage.exists())

    def test_exists_returns_false_when_file_does_not_exist(self):
        """Test exists() returns False when file doesn't exist"""
        storage = ExcelSLAStorage(self.test_file)
        self.assertFalse(storage.exists())

    def test_get_file_path_returns_correct_path(self):
        """Test get_file_path() returns the file path"""
        storage = ExcelSLAStorage(self.test_file)
        self.assertEqual(storage.get_file_path(), self.test_file)

    def test_write_creates_excel_file(self):
        """Test write() creates Excel file with data"""
        storage = ExcelSLAStorage(self.test_file)

        # Create test DataFrame
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Idea 1', 'Idea 2'],
            'created_at': [datetime(2025, 1, 1), datetime(2025, 1, 2)]
        })

        storage.write(df)

        # Verify file was created
        self.assertTrue(os.path.exists(self.test_file))

    def test_read_raises_error_when_file_not_found(self):
        """Test read() raises FileNotFoundError when file doesn't exist"""
        storage = ExcelSLAStorage(self.test_file)

        with self.assertRaises(FileNotFoundError):
            storage.read()


class TestGoogleSheetsSLAStorage(unittest.TestCase):
    """Tests for Google Sheets storage implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.credentials_file = 'test_credentials.json'
        self.sheet_id = 'test_sheet_id_123'
        self.sheet_name = 'SLA Tracking'

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_init_authenticates_successfully(self, mock_exists, mock_creds, mock_gspread):
        """Test __init__ authenticates and validates access"""
        # Mock file exists
        mock_exists.return_value = True

        # Mock credentials
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        # Mock gspread client and spreadsheet
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Verify authentication flow
        mock_exists.assert_called_with(self.credentials_file)
        mock_creds.from_service_account_file.assert_called_once()
        mock_gspread.authorize.assert_called_once_with(mock_creds_instance)
        mock_client.open_by_key.assert_called_once_with(self.sheet_id)

        self.assertEqual(storage.sheet_id, self.sheet_id)
        self.assertEqual(storage.sheet_name, self.sheet_name)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', False)
    def test_init_raises_import_error_when_gspread_not_available(self):
        """Test __init__ raises ImportError when gspread not installed"""
        with self.assertRaises(ImportError) as context:
            GoogleSheetsSLAStorage(
                self.credentials_file,
                self.sheet_id,
                self.sheet_name
            )

        self.assertIn('gspread', str(context.exception))
        self.assertIn('google-auth', str(context.exception))

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('os.path.exists')
    def test_init_raises_error_when_credentials_file_not_found(self, mock_exists):
        """Test __init__ raises FileNotFoundError when credentials file missing"""
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError) as context:
            GoogleSheetsSLAStorage(
                self.credentials_file,
                self.sheet_id,
                self.sheet_name
            )

        self.assertIn(self.credentials_file, str(context.exception))

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_init_raises_error_when_spreadsheet_not_found(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test __init__ raises error when spreadsheet not accessible"""
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_gspread.authorize.return_value = mock_client

        # Simulate spreadsheet not found
        mock_gspread.exceptions = MagicMock()
        mock_gspread.exceptions.SpreadsheetNotFound = Exception
        mock_client.open_by_key.side_effect = Exception("Spreadsheet not found")

        with self.assertRaises(Exception) as context:
            GoogleSheetsSLAStorage(
                self.credentials_file,
                self.sheet_id,
                self.sheet_name
            )

        self.assertIn('not found or not accessible', str(context.exception))

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_exists_returns_true_when_sheet_exists(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test exists() returns True when sheet/tab exists"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage and test exists
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        result = storage.exists()

        self.assertTrue(result)
        mock_spreadsheet.worksheet.assert_called_with(self.sheet_name)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_exists_returns_false_when_sheet_not_found(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test exists() returns False when sheet/tab doesn't exist"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Simulate worksheet not found
        mock_gspread.exceptions = MagicMock()
        mock_gspread.exceptions.WorksheetNotFound = Exception
        mock_spreadsheet.worksheet.side_effect = Exception("Worksheet not found")

        # Create storage and test exists
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        result = storage.exists()

        self.assertFalse(result)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_read_returns_dataframe_with_data(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test read() returns DataFrame with parsed data"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Mock sheet data
        mock_worksheet.get_all_values.return_value = [
            ['id', 'name', 'created_at', 'currently_meets_response_sla'],
            ['1', 'Idea 1', '2025-01-01 10:00:00', 'True'],
            ['2', 'Idea 2', '2025-01-02 11:00:00', 'False']
        ]

        # Create storage and read
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        df = storage.read()

        # Verify DataFrame structure
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['id', 'name', 'created_at', 'currently_meets_response_sla'])

        # Verify data types
        self.assertEqual(df['id'].dtype, 'Int64')
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['created_at']))
        self.assertEqual(df['currently_meets_response_sla'].tolist(), [True, False])

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_read_returns_empty_dataframe_when_sheet_empty(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test read() returns empty DataFrame when sheet is empty"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Mock empty sheet
        mock_worksheet.get_all_values.return_value = []

        # Create storage and read
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        df = storage.read()

        # Verify empty DataFrame
        self.assertEqual(len(df), 0)
        self.assertTrue(df.empty)

    # Note: Testing gspread-specific exception handling is challenging in unit tests
    # because the except clauses are evaluated at import time (can't mock after import).
    # The following error paths need integration testing (Phase 11):
    # - read() when worksheet doesn't exist (should raise Exception with available sheets)
    # - write() auto-creating worksheet when it doesn't exist (WorksheetNotFound handling)
    # - exists() catching WorksheetNotFound correctly
    # See plan.md Phase 11 for integration test requirements.

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_clears_existing_data_before_writing(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() clears sheet before writing (clear-and-rewrite behavior)"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create test DataFrame
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Idea 1', 'Idea 2']
        })

        # Write data
        storage.write(df)

        # Verify clear was called before writing
        mock_worksheet.clear.assert_called_once()

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_formats_dates_correctly(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() formats date columns as 'yyyy-mm-dd hh:mm:ss'"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create test DataFrame with date columns
        df = pd.DataFrame({
            'id': [1],
            'created_at': [datetime(2025, 1, 15, 10, 30, 45)],
            'response_sla': [datetime(2025, 1, 20, 12, 0, 0)]
        })

        # Write data
        storage.write(df)

        # Get the data that was written
        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify date formatting
        # Header row + data row
        self.assertEqual(len(written_data), 2)
        # Check date format in data row
        self.assertEqual(written_data[1][1], '2025-01-15 10:30:45')
        self.assertEqual(written_data[1][2], '2025-01-20 12:00:00')

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_get_file_path_returns_full_url(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test get_file_path() returns full Google Sheets URL"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Get file path
        url = storage.get_file_path()

        # Verify URL format
        expected_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
        self.assertEqual(url, expected_url)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_empty_dataframe(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() handles empty DataFrame (edge case - might crash with 0 columns)"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create empty DataFrame
        df = pd.DataFrame()

        # Write should handle empty DataFrame without crashing
        storage.write(df)

        # Verify clear was called
        mock_worksheet.clear.assert_called_once()

        # Verify update was called with just empty list (no headers, no data)
        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]
        self.assertEqual(written_data, [[]])  # Empty columns list + empty data

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_read_with_invalid_data_types(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test read() handles invalid data types gracefully (coerces to NaN/NaT)"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Mock sheet data with invalid types
        mock_worksheet.get_all_values.return_value = [
            ['id', 'name', 'created_at', 'currently_meets_response_sla'],
            ['abc', 'Invalid ID', 'not-a-date', 'maybe'],  # All invalid
            ['123', 'Valid ID', '2025-01-01 10:00:00', 'True']  # Valid
        ]

        # Create storage and read
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        df = storage.read()

        # Verify data types and coercion behavior
        self.assertEqual(len(df), 2)

        # Row 1: Invalid data should be coerced
        self.assertTrue(pd.isna(df.loc[0, 'id']))  # 'abc' → pd.NA
        self.assertTrue(pd.isna(df.loc[0, 'created_at']))  # 'not-a-date' → NaT
        self.assertTrue(pd.isna(df.loc[0, 'currently_meets_response_sla']))  # 'maybe' → NaN (not in map)

        # Row 2: Valid data should parse correctly
        self.assertEqual(df.loc[1, 'id'], 123)
        self.assertTrue(pd.notna(df.loc[1, 'created_at']))
        self.assertEqual(df.loc[1, 'currently_meets_response_sla'], True)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_read_with_mixed_case_booleans(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test read() handles various boolean string formats"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Mock sheet data with different boolean formats
        mock_worksheet.get_all_values.return_value = [
            ['id', 'currently_meets_response_sla', 'currently_meets_roadmap_sla'],
            ['1', 'True', 'False'],   # Title case
            ['2', 'TRUE', 'FALSE'],   # Upper case
            ['3', 'true', 'false'],   # Lower case (not in map - should be None)
        ]

        # Create storage and read
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        df = storage.read()

        # Verify boolean parsing
        self.assertEqual(df.loc[0, 'currently_meets_response_sla'], True)
        self.assertEqual(df.loc[0, 'currently_meets_roadmap_sla'], False)
        self.assertEqual(df.loc[1, 'currently_meets_response_sla'], True)
        self.assertEqual(df.loc[1, 'currently_meets_roadmap_sla'], False)
        # Lower case not in map - becomes NaN (pandas standard for missing)
        self.assertTrue(pd.isna(df.loc[2, 'currently_meets_response_sla']))
        self.assertTrue(pd.isna(df.loc[2, 'currently_meets_roadmap_sla']))

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_with_none_and_nan_values(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() handles None and NaN values correctly"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with None and NaN values
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Idea 1', None, 'Idea 3'],
            'value': [10.5, float('nan'), 30.0],
            'created_at': [datetime(2025, 1, 1), pd.NaT, datetime(2025, 1, 3)]
        })

        # Write data
        storage.write(df)

        # Get the data that was written
        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify None/NaN converted to empty strings
        self.assertEqual(len(written_data), 4)  # Header + 3 rows
        self.assertEqual(written_data[2][1], '')  # None → ''
        self.assertEqual(written_data[2][2], '')  # NaN → ''
        self.assertEqual(written_data[2][3], '')  # NaT → ''

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_read_with_only_headers_no_data(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test read() handles sheet with only headers (no data rows)"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Mock sheet data with only headers
        mock_worksheet.get_all_values.return_value = [
            ['id', 'name', 'created_at', 'currently_meets_response_sla']
            # No data rows
        ]

        # Create storage and read
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        df = storage.read()

        # Verify DataFrame has columns but no rows
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), ['id', 'name', 'created_at', 'currently_meets_response_sla'])
        self.assertTrue(df.empty)

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_with_complex_types_serializes_to_strings(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() converts lists and dicts to strings to avoid gspread errors"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create DataFrame with complex types (lists, dicts)
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Idea 1', 'Idea 2', 'Idea 3'],
            'tags': [['tag1', 'tag2'], [], ['tag3']],  # Lists
            'metadata': [{'key': 'value'}, {}, None],  # Dicts
            'team_ids': [[1, 2, 3], [4], None]  # Lists with None
        })

        # Write data
        storage.write(df)

        # Get the data that was written
        call_args = mock_worksheet.update.call_args
        written_data = call_args[0][0]

        # Verify complex types are converted to strings
        self.assertEqual(len(written_data), 4)  # Header + 3 rows

        # Row 1: lists and dicts converted to string representations
        self.assertEqual(written_data[1][2], "['tag1', 'tag2']")
        self.assertEqual(written_data[1][3], "{'key': 'value'}")
        self.assertEqual(written_data[1][4], "[1, 2, 3]")

        # Row 2: empty lists and dicts
        self.assertEqual(written_data[2][2], "[]")
        self.assertEqual(written_data[2][3], "{}")
        self.assertEqual(written_data[2][4], "[4]")

        # Row 3: None values converted to empty strings
        self.assertEqual(written_data[3][2], "['tag3']")
        self.assertEqual(written_data[3][3], '')  # None → ''
        self.assertEqual(written_data[3][4], '')  # None → ''

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    def test_write_handles_column_width_adjustment_failure_gracefully(
        self, mock_exists, mock_creds, mock_gspread
    ):
        """Test write() continues successfully even if column width adjustment fails"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance

        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Make update_column_width raise an AttributeError (method not available)
        mock_worksheet.update_column_width.side_effect = AttributeError("Method not supported")

        # Create storage
        storage = GoogleSheetsSLAStorage(
            self.credentials_file,
            self.sheet_id,
            self.sheet_name
        )

        # Create test DataFrame
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Idea 1', 'Idea 2'],
            'description': ['Short', 'This is a much longer description']
        })

        # Write should succeed despite column width adjustment failure
        storage.write(df)

        # Verify data was written (update was called)
        mock_worksheet.update.assert_called_once()

        # Verify clear was called
        mock_worksheet.clear.assert_called_once()

        # Verify format was called (header bold)
        mock_worksheet.format.assert_called_once()


class TestCreateStorageFactory(unittest.TestCase):
    """Tests for create_storage() factory function"""

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_with_output_path_returns_excel(self, mock_config):
        """Test that providing output_path returns ExcelSLAStorage (implicit override)"""
        from productplan_api_tools.sla.storage import create_storage, ExcelSLAStorage

        storage = create_storage(output_path="files/custom.xlsx")

        self.assertIsInstance(storage, ExcelSLAStorage)
        self.assertEqual(storage.get_file_path(), "files/custom.xlsx")
        # Should not check Google config when output_path specified
        mock_config.get_google_sheets_config.assert_not_called()

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_with_output_type_excel_returns_excel(self, mock_config):
        """Test that output_type='excel' returns ExcelSLAStorage (explicit override)"""
        from productplan_api_tools.sla.storage import create_storage, ExcelSLAStorage

        storage = create_storage(output_type="excel")

        self.assertIsInstance(storage, ExcelSLAStorage)
        self.assertEqual(storage.get_file_path(), "files/sla_tracking.xlsx")
        # Should not check Google config when output_type='excel'
        mock_config.get_google_sheets_config.assert_not_called()

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_auto_with_no_google_config_returns_excel(self, mock_config):
        """Test that output_type='auto' without Google config returns Excel (default fallback)"""
        from productplan_api_tools.sla.storage import create_storage, ExcelSLAStorage

        mock_config.get_google_sheets_config.return_value = None

        storage = create_storage(output_type="auto")

        self.assertIsInstance(storage, ExcelSLAStorage)
        self.assertEqual(storage.get_file_path(), "files/sla_tracking.xlsx")
        mock_config.get_google_sheets_config.assert_called_once()

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_auto_with_google_config_returns_sheets(
        self, mock_config, mock_exists, mock_creds, mock_gspread
    ):
        """Test that output_type='auto' with Google config returns GoogleSheetsSLAStorage"""
        from productplan_api_tools.sla.storage import create_storage, GoogleSheetsSLAStorage

        # Setup Google Sheets mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Mock config to return Google Sheets configuration
        mock_config.get_google_sheets_config.return_value = {
            'credentials_file': 'creds.json',
            'sheet_id': 'sheet123',
            'sheet_name': 'SLA Tracking'
        }

        storage = create_storage(output_type="auto")

        self.assertIsInstance(storage, GoogleSheetsSLAStorage)
        self.assertEqual(storage.get_file_path(), "https://docs.google.com/spreadsheets/d/sheet123")
        mock_config.get_google_sheets_config.assert_called_once()

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_sheets_without_config_raises_error(self, mock_config):
        """Test that output_type='sheets' without config raises ValueError"""
        from productplan_api_tools.sla.storage import create_storage

        mock_config.get_google_sheets_config.return_value = None

        with self.assertRaises(ValueError) as context:
            create_storage(output_type="sheets")

        self.assertIn("Google Sheets not configured", str(context.exception))
        self.assertIn("env/.env", str(context.exception))

    @patch('productplan_api_tools.sla.storage.GSPREAD_AVAILABLE', True)
    @patch('productplan_api_tools.sla.storage.gspread')
    @patch('productplan_api_tools.sla.storage.Credentials')
    @patch('os.path.exists')
    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_sheets_with_config_returns_sheets(
        self, mock_config, mock_exists, mock_creds, mock_gspread
    ):
        """Test that output_type='sheets' with config returns GoogleSheetsSLAStorage"""
        from productplan_api_tools.sla.storage import create_storage, GoogleSheetsSLAStorage

        # Setup Google Sheets mocks
        mock_exists.return_value = True
        mock_creds_instance = Mock()
        mock_creds.from_service_account_file.return_value = mock_creds_instance
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_gspread.authorize.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet

        # Mock config to return Google Sheets configuration
        mock_config.get_google_sheets_config.return_value = {
            'credentials_file': 'creds.json',
            'sheet_id': 'sheet456',
            'sheet_name': 'SLA Data'
        }

        storage = create_storage(output_type="sheets")

        self.assertIsInstance(storage, GoogleSheetsSLAStorage)
        self.assertEqual(storage.get_file_path(), "https://docs.google.com/spreadsheets/d/sheet456")

    def test_create_storage_invalid_output_type_raises_error(self):
        """Test that invalid output_type raises ValueError"""
        from productplan_api_tools.sla.storage import create_storage

        with self.assertRaises(ValueError) as context:
            create_storage(output_type="invalid")

        self.assertIn("Invalid output_type", str(context.exception))
        self.assertIn("'auto', 'excel', or 'sheets'", str(context.exception))

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_output_path_takes_precedence_over_type(self, mock_config):
        """Test that output_path overrides output_type (implicit > explicit)"""
        from productplan_api_tools.sla.storage import create_storage, ExcelSLAStorage

        # Even with output_type="sheets", output_path should take precedence
        storage = create_storage(output_path="files/override.xlsx", output_type="sheets")

        self.assertIsInstance(storage, ExcelSLAStorage)
        self.assertEqual(storage.get_file_path(), "files/override.xlsx")
        # Should not check Google config when output_path specified
        mock_config.get_google_sheets_config.assert_not_called()

    @patch('productplan_api_tools.sla.storage.config')
    def test_create_storage_default_behavior(self, mock_config):
        """Test default behavior with no arguments (should check config and fallback to Excel)"""
        from productplan_api_tools.sla.storage import create_storage, ExcelSLAStorage

        mock_config.get_google_sheets_config.return_value = None

        storage = create_storage()

        self.assertIsInstance(storage, ExcelSLAStorage)
        self.assertEqual(storage.get_file_path(), "files/sla_tracking.xlsx")
        mock_config.get_google_sheets_config.assert_called_once()


if __name__ == '__main__':
    unittest.main()
