"""
Unit tests for SLA storage layer

Tests storage interface and Excel implementation with temporary files.
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime
from pathlib import Path

from productplan_api_tools.sla.storage import ExcelSLAStorage


class TestExcelSLAStorage:
    """Tests for ExcelSLAStorage class"""

    @pytest.fixture
    def temp_excel_file(self):
        """Create a temporary Excel file path"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            file_path = tmp.name

        yield file_path

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame with SLA tracking data"""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Idea 1', 'Idea 2', 'Idea 3'],
            'description': ['Description 1', 'Description 2', 'Description 3'],
            'customer': ['Customer A', 'Customer B', 'Customer C'],
            'source_name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'source_email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
            'created_at': [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 15, 14, 30, 0),
                datetime(2024, 2, 1, 9, 15, 0)
            ],
            'updated_at': [
                datetime(2024, 1, 10, 12, 0, 0),
                datetime(2024, 1, 20, 16, 0, 0),
                datetime(2024, 2, 5, 11, 30, 0)
            ],
            'idea_status': ['Accepted', 'In Review', 'On deck'],
            'location_status': ['visible', 'visible', 'visible'],
            'Engineering': [1, 0, 1],
            'Product': [1, 1, 0],
            'response_sla': [
                datetime(2024, 1, 8, 10, 0, 0),
                datetime(2024, 1, 16, 14, 30, 0),
                None
            ],
            'roadmap_sla': [
                datetime(2024, 1, 25, 10, 0, 0),
                None,
                None
            ],
            'currently_meets_response_sla': [True, True, False],
            'currently_meets_roadmap_sla': [True, False, False]
        })

    def test_exists_returns_false_for_nonexistent_file(self, temp_excel_file):
        """Test exists() returns False when file doesn't exist"""
        # Delete the temp file so it doesn't exist
        if os.path.exists(temp_excel_file):
            os.remove(temp_excel_file)

        storage = ExcelSLAStorage(temp_excel_file)
        assert storage.exists() is False

    def test_exists_returns_true_for_existing_file(self, temp_excel_file, sample_dataframe):
        """Test exists() returns True when file exists"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Create the file
        storage.write(sample_dataframe)

        assert storage.exists() is True

    def test_write_creates_new_file(self, temp_excel_file, sample_dataframe):
        """Test write() creates a new Excel file"""
        # Ensure file doesn't exist
        if os.path.exists(temp_excel_file):
            os.remove(temp_excel_file)

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        assert os.path.exists(temp_excel_file)
        assert os.path.getsize(temp_excel_file) > 0

    def test_read_write_roundtrip_preserves_data(self, temp_excel_file, sample_dataframe):
        """Test that writing and reading back preserves ALL data in ALL columns"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Write data
        storage.write(sample_dataframe)

        # Read it back
        df_read = storage.read()

        # Verify basic structure
        assert len(df_read) == len(sample_dataframe)
        assert list(df_read.columns) == list(sample_dataframe.columns)

        # Verify ALL columns (not just a sample!)

        # Integer columns
        assert df_read['id'].tolist() == [1, 2, 3]
        assert df_read['Engineering'].tolist() == [1, 0, 1]
        assert df_read['Product'].tolist() == [1, 1, 0]

        # String columns
        assert df_read['name'].tolist() == ['Idea 1', 'Idea 2', 'Idea 3']
        assert df_read['description'].tolist() == ['Description 1', 'Description 2', 'Description 3']
        assert df_read['customer'].tolist() == ['Customer A', 'Customer B', 'Customer C']
        assert df_read['source_name'].tolist() == ['John Doe', 'Jane Smith', 'Bob Johnson']
        assert df_read['source_email'].tolist() == ['john@example.com', 'jane@example.com', 'bob@example.com']
        assert df_read['idea_status'].tolist() == ['Accepted', 'In Review', 'On deck']
        assert df_read['location_status'].tolist() == ['visible', 'visible', 'visible']

        # Boolean columns
        assert df_read['currently_meets_response_sla'].tolist() == [True, True, False]
        assert df_read['currently_meets_roadmap_sla'].tolist() == [True, False, False]

        # Date columns (spot check - detailed date testing in separate test)
        assert pd.api.types.is_datetime64_any_dtype(df_read['created_at'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['updated_at'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['response_sla'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['roadmap_sla'])

        # Verify date values for first row
        assert df_read.loc[0, 'created_at'] == sample_dataframe.loc[0, 'created_at']
        assert df_read.loc[0, 'updated_at'] == sample_dataframe.loc[0, 'updated_at']

        # Verify null handling in date columns
        assert pd.notna(df_read.loc[0, 'response_sla'])
        assert pd.isna(df_read.loc[2, 'response_sla'])  # Third row should be null

    def test_date_columns_formatted_as_excel_dates(self, temp_excel_file, sample_dataframe):
        """Test that date columns are formatted as Excel dates"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        # Read back and verify datetime types are preserved
        df_read = storage.read()

        # Check date columns are datetime type (or NaT for None values)
        assert pd.api.types.is_datetime64_any_dtype(df_read['created_at'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['updated_at'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['response_sla'])
        assert pd.api.types.is_datetime64_any_dtype(df_read['roadmap_sla'])

    def test_date_values_preserved_after_roundtrip(self, temp_excel_file, sample_dataframe):
        """Test that date values are correctly preserved"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)
        df_read = storage.read()

        # Compare datetime values (accounting for potential microsecond differences)
        for i in range(len(sample_dataframe)):
            # created_at
            original_created = sample_dataframe.loc[i, 'created_at']
            read_created = df_read.loc[i, 'created_at']
            assert abs((original_created - read_created).total_seconds()) < 1

            # response_sla (first row has a value)
            if i == 0:
                original_response = sample_dataframe.loc[i, 'response_sla']
                read_response = df_read.loc[i, 'response_sla']
                assert abs((original_response - read_response).total_seconds()) < 1

    def test_column_ordering_matches_specification(self, temp_excel_file, sample_dataframe):
        """Test that column ordering is preserved"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)
        df_read = storage.read()

        # Verify column order matches input
        assert list(df_read.columns) == list(sample_dataframe.columns)

    def test_team_columns_binary_values_preserved(self, temp_excel_file, sample_dataframe):
        """Test that team columns (1/0) are preserved correctly"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)
        df_read = storage.read()

        # Check Engineering column
        assert df_read['Engineering'].tolist() == [1, 0, 1]

        # Check Product column
        assert df_read['Product'].tolist() == [1, 1, 0]

    def test_boolean_columns_preserved(self, temp_excel_file, sample_dataframe):
        """Test that boolean columns are preserved correctly"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)
        df_read = storage.read()

        # Check boolean columns
        assert df_read['currently_meets_response_sla'].tolist() == [True, True, False]
        assert df_read['currently_meets_roadmap_sla'].tolist() == [True, False, False]

    def test_read_raises_error_for_nonexistent_file(self, temp_excel_file):
        """Test that read() raises FileNotFoundError for missing file"""
        # Ensure file doesn't exist
        if os.path.exists(temp_excel_file):
            os.remove(temp_excel_file)

        storage = ExcelSLAStorage(temp_excel_file)

        with pytest.raises(FileNotFoundError) as exc_info:
            storage.read()

        assert "SLA tracking file not found" in str(exc_info.value)

    def test_write_creates_directory_if_missing(self, sample_dataframe):
        """Test that write() creates parent directory if it doesn't exist"""
        # Create a path with a non-existent directory
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, 'subdir', 'sla_tracking.xlsx')

            storage = ExcelSLAStorage(nested_path)

            # Directory shouldn't exist yet
            assert not os.path.exists(os.path.dirname(nested_path))

            # Write should create directory and file
            storage.write(sample_dataframe)

            assert os.path.exists(os.path.dirname(nested_path))
            assert os.path.exists(nested_path)

    def test_get_file_path_returns_correct_path(self, temp_excel_file):
        """Test that get_file_path() returns the file path"""
        storage = ExcelSLAStorage(temp_excel_file)
        assert storage.get_file_path() == temp_excel_file

    def test_empty_dataframe_handling(self, temp_excel_file):
        """Test handling of empty DataFrame"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Create empty DataFrame with columns
        empty_df = pd.DataFrame(columns=['id', 'name', 'created_at'])

        storage.write(empty_df)
        df_read = storage.read()

        assert len(df_read) == 0
        assert list(df_read.columns) == ['id', 'name', 'created_at']

    def test_null_values_in_date_columns(self, temp_excel_file):
        """Test handling of null/None values in date columns"""
        df_with_nulls = pd.DataFrame({
            'id': [1, 2],
            'created_at': [datetime(2024, 1, 1), datetime(2024, 1, 15)],
            'response_sla': [datetime(2024, 1, 8), None],  # Second row has None
            'roadmap_sla': [None, None]  # All None
        })

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(df_with_nulls)
        df_read = storage.read()

        # Verify nulls are preserved
        assert pd.isna(df_read.loc[1, 'response_sla'])
        assert pd.isna(df_read.loc[0, 'roadmap_sla'])
        assert pd.isna(df_read.loc[1, 'roadmap_sla'])

    def test_large_text_values(self, temp_excel_file):
        """Test handling of large text values in description field"""
        large_text = 'A' * 1000  # 1000 character string

        df = pd.DataFrame({
            'id': [1],
            'description': [large_text],
            'created_at': [datetime(2024, 1, 1)]
        })

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(df)
        df_read = storage.read()

        # Verify large text is preserved
        assert df_read.loc[0, 'description'] == large_text
        assert len(df_read.loc[0, 'description']) == 1000

    def test_data_type_preservation(self, temp_excel_file):
        """Test that data types are preserved after roundtrip (int stays int, not float)"""
        df = pd.DataFrame({
            'id': [1, 2, 3],  # Integer
            'score': [10, 20, 30],  # Integer
            'name': ['A', 'B', 'C'],  # String
            'is_active': [True, False, True],  # Boolean
            'created_at': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]  # Datetime
        })

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(df)
        df_read = storage.read()

        # Verify integer columns stay integers (not converted to floats)
        assert df_read['id'].dtype == 'int64' or df_read['id'].dtype == 'int32', \
            f"Expected int64/int32, got {df_read['id'].dtype}"
        assert df_read['score'].dtype == 'int64' or df_read['score'].dtype == 'int32'

        # Verify string columns stay strings (object dtype in pandas)
        assert df_read['name'].dtype == 'object'

        # Verify boolean columns stay booleans
        assert df_read['is_active'].dtype == 'bool'

        # Verify datetime columns stay datetime
        assert pd.api.types.is_datetime64_any_dtype(df_read['created_at'])

        # Verify actual values match
        assert df_read['id'].tolist() == [1, 2, 3]
        assert df_read['is_active'].tolist() == [True, False, True]

    def test_none_dataframe_input(self, temp_excel_file):
        """Test that passing None to write raises appropriate error"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Should raise an error when trying to write None
        with pytest.raises(Exception):  # Could be AttributeError or ValueError
            storage.write(None)

    def test_dataframe_with_no_columns(self, temp_excel_file):
        """Test handling DataFrame with no columns at all"""
        df = pd.DataFrame()  # No columns, no data

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(df)
        df_read = storage.read()

        # Should handle gracefully
        assert len(df_read) == 0
        assert len(df_read.columns) == 0

    def test_special_characters_in_strings(self, temp_excel_file):
        """Test handling of special characters in string data"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': [
                "Idea with 'single quotes'",
                'Idea with "double quotes"',
                "Idea with\nnewlines\nand\ttabs"
            ],
            'description': [
                "Contains: semicolon; comma, pipe|",
                "Math symbols: + - * / = < >",
                "Special chars: @#$%^&*()"
            ]
        })

        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(df)
        df_read = storage.read()

        # Verify special characters are preserved exactly
        assert df_read['name'].tolist() == [
            "Idea with 'single quotes'",
            'Idea with "double quotes"',
            "Idea with\nnewlines\nand\ttabs"
        ]
        assert df_read['description'].tolist() == [
            "Contains: semicolon; comma, pipe|",
            "Math symbols: + - * / = < >",
            "Special chars: @#$%^&*()"
        ]

    def test_record_run_creates_runs_sheet_on_first_call(self, temp_excel_file, sample_dataframe):
        """Test that record_run() creates Runs sheet on first call"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Write main data first
        storage.write(sample_dataframe)

        # Record a run
        storage.record_run('init', records_added=3, records_updated=0)

        # Read the Runs sheet
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify structure
        assert list(runs_df.columns) == ['type', 'timestamp', 'records_added', 'records_updated']
        assert len(runs_df) == 1

        # Verify data
        assert runs_df.loc[0, 'type'] == 'init'
        assert runs_df.loc[0, 'records_added'] == 3
        assert runs_df.loc[0, 'records_updated'] == 0

        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        timestamp = runs_df.loc[0, 'timestamp']
        assert isinstance(timestamp, str)
        assert len(timestamp) == 19  # "YYYY-MM-DD HH:MM:SS" is 19 chars
        assert timestamp[4] == '-'
        assert timestamp[7] == '-'
        assert timestamp[10] == ' '
        assert timestamp[13] == ':'
        assert timestamp[16] == ':'

    def test_record_run_appends_to_existing_runs_sheet(self, temp_excel_file, sample_dataframe):
        """Test that record_run() appends to existing Runs sheet"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Write main data first
        storage.write(sample_dataframe)

        # Record multiple runs
        storage.record_run('init', records_added=3, records_updated=0)
        storage.record_run('update', records_added=1, records_updated=2)
        storage.record_run('update', records_added=0, records_updated=3)

        # Read the Runs sheet
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify all runs are recorded
        assert len(runs_df) == 3

        # Verify first run
        assert runs_df.loc[0, 'type'] == 'init'
        assert runs_df.loc[0, 'records_added'] == 3
        assert runs_df.loc[0, 'records_updated'] == 0

        # Verify second run
        assert runs_df.loc[1, 'type'] == 'update'
        assert runs_df.loc[1, 'records_added'] == 1
        assert runs_df.loc[1, 'records_updated'] == 2

        # Verify third run
        assert runs_df.loc[2, 'type'] == 'update'
        assert runs_df.loc[2, 'records_added'] == 0
        assert runs_df.loc[2, 'records_updated'] == 3

    def test_record_run_preserves_main_data_sheet(self, temp_excel_file, sample_dataframe):
        """Test that record_run() doesn't affect the main SLA Tracking sheet"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Write main data
        storage.write(sample_dataframe)

        # Read main data to compare later
        df_before = storage.read()

        # Record a run
        storage.record_run('init', records_added=3, records_updated=0)

        # Read main data again
        df_after = storage.read()

        # Verify main data is unchanged
        assert len(df_before) == len(df_after)
        assert list(df_before.columns) == list(df_after.columns)
        assert df_before['id'].tolist() == df_after['id'].tolist()
        assert df_before['name'].tolist() == df_after['name'].tolist()

    def test_record_run_with_new_file_creates_both_sheets(self, temp_excel_file):
        """Test that record_run() works even when called on a new file (shouldn't normally happen)"""
        # Delete temp file to ensure it doesn't exist
        if os.path.exists(temp_excel_file):
            os.remove(temp_excel_file)

        storage = ExcelSLAStorage(temp_excel_file)

        # Record a run on a non-existent file (edge case)
        storage.record_run('init', records_added=5, records_updated=0)

        # Verify file was created with Runs sheet
        assert os.path.exists(temp_excel_file)
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify data
        assert len(runs_df) == 1
        assert runs_df.loc[0, 'type'] == 'init'
        assert runs_df.loc[0, 'records_added'] == 5
        assert runs_df.loc[0, 'records_updated'] == 0

    def test_record_run_timestamp_is_utc_format(self, temp_excel_file, sample_dataframe):
        """Test that record_run() uses UTC timestamp format"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        # Record a run
        storage.record_run('init', records_added=1, records_updated=0)

        # Read runs sheet
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify timestamp is a valid datetime string
        timestamp_str = runs_df.loc[0, 'timestamp']

        # Parse timestamp to verify it's valid
        from datetime import datetime as dt
        parsed = dt.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        # Verify it's close to current UTC time (within 10 seconds)
        from datetime import datetime
        now_utc = datetime.utcnow()
        time_diff = abs((now_utc - parsed).total_seconds())
        assert time_diff < 10, f"Timestamp {timestamp_str} is not close to current UTC time"

    def test_record_run_with_zero_counts(self, temp_excel_file, sample_dataframe):
        """Test that record_run() handles zero counts correctly"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        # Record run with zero counts
        storage.record_run('update', records_added=0, records_updated=0)

        # Read runs sheet
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify zeros are preserved
        assert runs_df.loc[0, 'records_added'] == 0
        assert runs_df.loc[0, 'records_updated'] == 0

    def test_record_run_with_large_counts(self, temp_excel_file, sample_dataframe):
        """Test that record_run() handles large record counts"""
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        # Record run with large counts
        storage.record_run('init', records_added=9999, records_updated=8888)

        # Read runs sheet
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')

        # Verify large numbers are preserved
        assert runs_df.loc[0, 'records_added'] == 9999
        assert runs_df.loc[0, 'records_updated'] == 8888

    def test_write_preserves_runs_sheet_after_record_run(self, temp_excel_file, sample_dataframe):
        """CRITICAL: Test that write() preserves Runs sheet (regression test for bug fix)"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Initial write and record run
        storage.write(sample_dataframe)
        storage.record_run('init', records_added=3, records_updated=0)

        # Verify Runs sheet exists with 1 row
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')
        assert len(runs_df) == 1
        assert runs_df.loc[0, 'type'] == 'init'

        # Now call write() again (simulating sla_update workflow)
        # This should NOT destroy the Runs sheet
        modified_data = sample_dataframe.copy()
        modified_data.loc[0, 'name'] = 'Modified Idea'
        storage.write(modified_data)

        # Verify Runs sheet STILL exists with original data
        runs_df_after = pd.read_excel(temp_excel_file, sheet_name='Runs')
        assert len(runs_df_after) == 1, "Runs sheet was destroyed by write()!"
        assert runs_df_after.loc[0, 'type'] == 'init'
        assert runs_df_after.loc[0, 'records_added'] == 3

        # Verify main data was updated
        main_df = storage.read()
        assert main_df.loc[0, 'name'] == 'Modified Idea'

    def test_write_then_record_run_then_write_preserves_all_runs(self, temp_excel_file, sample_dataframe):
        """Test realistic workflow: write, record, write, record - all runs preserved"""
        storage = ExcelSLAStorage(temp_excel_file)

        # Step 1: Initial write + record (simulating sla-init)
        storage.write(sample_dataframe)
        storage.record_run('init', records_added=3, records_updated=0)

        # Step 2: Update write + record (simulating sla-update)
        modified_data = sample_dataframe.copy()
        modified_data.loc[0, 'name'] = 'Updated 1'
        storage.write(modified_data)
        storage.record_run('update', records_added=1, records_updated=2)

        # Step 3: Another update
        modified_data.loc[0, 'name'] = 'Updated 2'
        storage.write(modified_data)
        storage.record_run('update', records_added=0, records_updated=1)

        # Verify all 3 runs are preserved
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')
        assert len(runs_df) == 3, f"Expected 3 runs, got {len(runs_df)}"
        assert runs_df.loc[0, 'type'] == 'init'
        assert runs_df.loc[1, 'type'] == 'update'
        assert runs_df.loc[2, 'type'] == 'update'

    def test_record_run_timestamps_are_sequential(self, temp_excel_file, sample_dataframe):
        """Test that multiple runs have sequential (non-decreasing) timestamps"""
        import time
        storage = ExcelSLAStorage(temp_excel_file)
        storage.write(sample_dataframe)

        # Record three runs with small delays
        storage.record_run('init', records_added=1, records_updated=0)
        time.sleep(0.1)  # Small delay to ensure different timestamps
        storage.record_run('update', records_added=1, records_updated=0)
        time.sleep(0.1)
        storage.record_run('update', records_added=0, records_updated=1)

        # Read and verify timestamps
        runs_df = pd.read_excel(temp_excel_file, sheet_name='Runs')
        assert len(runs_df) == 3

        # Parse timestamps
        from datetime import datetime as dt
        ts1 = dt.strptime(runs_df.loc[0, 'timestamp'], '%Y-%m-%d %H:%M:%S')
        ts2 = dt.strptime(runs_df.loc[1, 'timestamp'], '%Y-%m-%d %H:%M:%S')
        ts3 = dt.strptime(runs_df.loc[2, 'timestamp'], '%Y-%m-%d %H:%M:%S')

        # Verify sequential ordering
        assert ts2 >= ts1, f"Second timestamp {ts2} is before first {ts1}"
        assert ts3 >= ts2, f"Third timestamp {ts3} is before second {ts2}"
