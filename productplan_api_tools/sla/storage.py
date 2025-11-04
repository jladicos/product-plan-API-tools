"""
SLA Storage

Storage abstraction layer for SLA tracking data.
Provides interface and implementations for reading/writing SLA spreadsheets.
"""

import os
from typing import Protocol, Optional
import pandas as pd
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# Import config for factory function
from productplan_api_tools import config


class SLAStorage(Protocol):
    """
    Protocol (interface) for SLA storage implementations

    This allows for multiple storage backends (Excel, Google Sheets, etc.)
    without changing business logic.
    """

    def exists(self) -> bool:
        """Check if the storage file/location exists"""
        ...

    def read(self) -> pd.DataFrame:
        """Read SLA data into a pandas DataFrame"""
        ...

    def write(self, df: pd.DataFrame) -> None:
        """Write pandas DataFrame to storage"""
        ...

    def get_file_path(self) -> str:
        """Get the storage file path or identifier"""
        ...


class ExcelSLAStorage:
    """
    Excel file implementation of SLA storage

    Handles reading/writing SLA tracking data to Excel files with proper
    date formatting and column ordering.
    """

    def __init__(self, file_path: str):
        """
        Initialize Excel storage

        Args:
            file_path: Absolute path to Excel file
        """
        self.file_path = file_path

    def exists(self) -> bool:
        """
        Check if Excel file exists

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(self.file_path)

    def read(self) -> pd.DataFrame:
        """
        Read Excel file into DataFrame

        Returns:
            DataFrame with SLA tracking data

        Raises:
            FileNotFoundError: If file doesn't exist

        Note:
            Date columns (created_at, updated_at, response_sla, roadmap_sla)
            are automatically parsed as datetime objects if they exist
        """
        if not self.exists():
            raise FileNotFoundError(f"SLA tracking file not found: {self.file_path}")

        # First read without date parsing to see what columns exist
        df = pd.read_excel(self.file_path)

        # List of potential date columns
        potential_date_columns = ['created_at', 'updated_at', 'response_sla', 'roadmap_sla']

        # Only parse date columns that actually exist in the DataFrame
        for col in potential_date_columns:
            if col in df.columns:
                # Convert to datetime, handling errors gracefully
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def write(self, df: pd.DataFrame) -> None:
        """
        Write DataFrame to Excel file with proper formatting

        Args:
            df: DataFrame to write

        Features:
            - Date columns formatted as Excel dates
            - Boolean columns formatted properly
            - Auto-adjusts column widths
            - Creates directory if it doesn't exist
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(self.file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Create Excel writer with openpyxl engine for formatting support
        # Use mode='a' if file exists AND is valid Excel file (to preserve other sheets like Runs)
        # Use mode='w' if file doesn't exist or is not a valid Excel file
        mode = 'w'
        if_sheet_exists = None

        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            # File exists and has content - try to open in append mode
            try:
                # Test if it's a valid Excel file by trying to read it
                pd.ExcelFile(self.file_path)
                mode = 'a'
                if_sheet_exists = 'replace'
            except:
                # Not a valid Excel file - use write mode
                mode = 'w'

        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode=mode, if_sheet_exists=if_sheet_exists) as writer:
            # Write DataFrame to Excel
            df.to_excel(writer, index=False, sheet_name='SLA Tracking')

            # Get worksheet for formatting
            worksheet = writer.sheets['SLA Tracking']

            # Format date columns as Excel dates
            date_columns = ['created_at', 'updated_at', 'response_sla', 'roadmap_sla']
            for col_name in date_columns:
                if col_name in df.columns:
                    col_idx = df.columns.get_loc(col_name) + 1  # Excel is 1-indexed
                    for row_idx in range(2, len(df) + 2):  # Start from row 2 (after header)
                        cell = worksheet.cell(row=row_idx, column=col_idx)
                        if cell.value is not None:
                            # Apply Excel date format
                            cell.number_format = 'yyyy-mm-dd hh:mm:ss'

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass

                # Set column width (add padding)
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width

    def get_file_path(self) -> str:
        """
        Get the Excel file path

        Returns:
            Absolute path to Excel file
        """
        return self.file_path

    def record_run(self, run_type: str, records_added: int, records_updated: int) -> None:
        """
        Record a run (init or update) in the Runs tracking sheet

        Appends a new row to the Runs sheet with execution details.
        Creates the Runs sheet if it doesn't exist.

        Args:
            run_type: Type of run ("init" or "update")
            records_added: Number of records added in this run
            records_updated: Number of records updated in this run

        Side effects:
            Appends row to "Runs" sheet in Excel workbook
        """
        from datetime import datetime
        from productplan_api_tools import config

        # Get runs sheet name from config
        runs_sheet_name = config.get_runs_sheet_name()

        # Get current timestamp in UTC
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Create DataFrame for this run
        run_data = pd.DataFrame({
            'type': [run_type],
            'timestamp': [timestamp],
            'records_added': [records_added],
            'records_updated': [records_updated]
        })

        # Read existing Excel file or create new workbook
        if os.path.exists(self.file_path):
            # Load existing workbook
            with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                # Check if Runs sheet exists
                if runs_sheet_name in writer.book.sheetnames:
                    # Read existing runs data
                    existing_runs = pd.read_excel(self.file_path, sheet_name=runs_sheet_name)
                    # Append new run
                    combined_runs = pd.concat([existing_runs, run_data], ignore_index=True)
                else:
                    # First run - just use new data
                    combined_runs = run_data

                # Write to Runs sheet
                combined_runs.to_excel(writer, sheet_name=runs_sheet_name, index=False)
        else:
            # File doesn't exist yet - this shouldn't happen in normal flow
            # but handle it gracefully
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                run_data.to_excel(writer, sheet_name=runs_sheet_name, index=False)


class GoogleSheetsSLAStorage:
    """
    Google Sheets implementation of SLA storage

    Handles reading/writing SLA tracking data to Google Sheets with proper
    date formatting and column ordering to match Excel output.

    Error Handling:
        - Fails fast on authentication errors (doesn't fallback silently)
        - Fails fast on missing/invalid spreadsheet (clear error message)
        - Auto-creates sheet/tab if it doesn't exist (matches Excel behavior)
    """

    def __init__(self, credentials_file: str, sheet_id: str, sheet_name: str):
        """
        Initialize Google Sheets storage

        Args:
            credentials_file: Path to Google service account JSON credentials
            sheet_id: Google Sheets document ID
            sheet_name: Name of sheet/tab within the document

        Raises:
            ImportError: If gspread or google-auth not installed
            FileNotFoundError: If credentials file doesn't exist
            Exception: If authentication fails or spreadsheet not accessible
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError(
                "Google Sheets support requires gspread and google-auth. "
                "Install with: pip install gspread google-auth"
            )

        if not os.path.exists(credentials_file):
            raise FileNotFoundError(
                f"Google credentials file not found: {credentials_file}"
            )

        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None

        # Authenticate and validate access (fail fast)
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with Google Sheets API and validate access

        Raises:
            Exception: If authentication fails or spreadsheet not accessible
        """
        try:
            # Define the scope for Google Sheets API
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Load credentials from service account file
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            # Create gspread client
            self._client = gspread.authorize(creds)

            # Open spreadsheet (this validates access)
            self._spreadsheet = self._client.open_by_key(self.sheet_id)

        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception(
                f"Google Spreadsheet not found or not accessible. "
                f"Sheet ID: {self.sheet_id}. "
                f"Make sure the service account has access to this spreadsheet."
            )
        except Exception as e:
            raise Exception(
                f"Failed to authenticate with Google Sheets: {str(e)}"
            )

    def exists(self) -> bool:
        """
        Check if the sheet/tab exists in the spreadsheet

        Returns:
            True if sheet/tab exists, False otherwise
        """
        try:
            self._spreadsheet.worksheet(self.sheet_name)
            return True
        except gspread.exceptions.WorksheetNotFound:
            return False

    def read(self) -> pd.DataFrame:
        """
        Read Google Sheet into DataFrame

        Returns:
            DataFrame with SLA tracking data

        Raises:
            Exception: If sheet/tab doesn't exist

        Note:
            Date columns (created_at, updated_at, response_sla, roadmap_sla)
            are automatically parsed as datetime objects if they exist
        """
        try:
            worksheet = self._spreadsheet.worksheet(self.sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            raise Exception(
                f"Sheet/tab '{self.sheet_name}' not found in spreadsheet. "
                f"Available sheets: {[ws.title for ws in self._spreadsheet.worksheets()]}"
            )

        # Get all values from sheet
        values = worksheet.get_all_values()

        if not values:
            # Empty sheet - return empty DataFrame
            return pd.DataFrame()

        # First row is header
        headers = values[0]
        data = values[1:]

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Convert empty strings to None for proper type conversion
        df = df.replace('', None)

        # Parse date columns if they exist
        potential_date_columns = ['created_at', 'updated_at', 'response_sla', 'roadmap_sla']
        for col in potential_date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Convert numeric columns (id, boolean columns)
        if 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')

        # Convert boolean columns
        boolean_columns = ['currently_meets_response_sla', 'currently_meets_roadmap_sla']
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].map({'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        return df

    def write(self, df: pd.DataFrame) -> None:
        """
        Write DataFrame to Google Sheet with proper formatting

        Behavior:
            - Clears entire sheet/tab before writing (like Excel mode='w')
            - Auto-creates sheet/tab if it doesn't exist
            - Formats date columns to match Excel
            - Auto-adjusts column widths (max 50 chars like Excel)

        Args:
            df: DataFrame to write

        Features:
            - Date columns formatted as 'yyyy-mm-dd hh:mm:ss'
            - Boolean columns formatted properly
            - Auto-adjusts column widths
            - Creates sheet/tab if it doesn't exist
        """
        # Get or create worksheet
        try:
            worksheet = self._spreadsheet.worksheet(self.sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Auto-create sheet/tab (matches Excel behavior of creating directories)
            worksheet = self._spreadsheet.add_worksheet(
                title=self.sheet_name,
                rows=len(df) + 1,
                cols=len(df.columns)
            )

        # Clear existing data (clear-and-rewrite behavior)
        worksheet.clear()

        # Format dates as strings for Google Sheets
        df_copy = df.copy()
        date_columns = ['created_at', 'updated_at', 'response_sla', 'roadmap_sla']
        for col in date_columns:
            if col in df_copy.columns:
                # Convert datetime to string with Excel-like format
                df_copy[col] = df_copy[col].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else ''
                )

        # Convert DataFrame to list of lists for gspread
        # Include header row
        # Convert all values to strings to avoid complex types (lists, dicts, etc.)
        header = [str(col) for col in df_copy.columns]

        # Convert each cell to a simple string/number
        data_rows = []
        for _, row in df_copy.iterrows():
            row_values = []
            for val in row:
                # Check for complex types FIRST (before pd.isna check)
                # because pd.isna() fails on lists/arrays with ambiguous truth value error
                if isinstance(val, (list, dict)):
                    # Convert complex types to string representation
                    # Always convert to string, even if empty ([] becomes "[]", not "")
                    row_values.append(str(val))
                elif val is None:
                    row_values.append('')
                elif pd.isna(val):
                    row_values.append('')
                else:
                    row_values.append(val)
            data_rows.append(row_values)

        values = [header] + data_rows

        # Write all data at once (more efficient)
        worksheet.update(values, 'A1')

        # Format header row (bold)
        worksheet.format('1:1', {'textFormat': {'bold': True}})

        # Auto-adjust column widths (match Excel behavior)
        # This is optional - if it fails, we still have the data
        try:
            for idx, col in enumerate(df.columns):
                # Calculate max length in column (including header)
                max_length = len(str(col))
                for value in df[col]:
                    if pd.notna(value):
                        max_length = max(max_length, len(str(value)))

                # Set column width (add padding, cap at 50 chars like Excel)
                adjusted_width = min(max_length + 2, 50) * 10  # Google Sheets uses pixels
                worksheet.update_column_width(idx, adjusted_width)
        except (AttributeError, Exception) as e:
            # Column width adjustment not supported or failed - not critical
            # Data is already written, just continue without width adjustment
            pass

    def get_file_path(self) -> str:
        """
        Get the Google Sheets URL for user-facing output

        Returns:
            Full URL to Google Sheets document
        """
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"

    def record_run(self, run_type: str, records_added: int, records_updated: int) -> None:
        """
        Record a run (init or update) in the Runs tracking sheet

        Appends a new row to the Runs sheet with execution details.
        Creates the Runs sheet if it doesn't exist.

        Args:
            run_type: Type of run ("init" or "update")
            records_added: Number of records added in this run
            records_updated: Number of records updated in this run

        Side effects:
            Appends row to Runs sheet in Google Sheets document
        """
        from datetime import datetime
        from productplan_api_tools import config

        # Get runs sheet name from config
        runs_sheet_name = config.get_runs_sheet_name()

        # Get current timestamp in UTC
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Create run record
        run_record = [run_type, timestamp, records_added, records_updated]

        # Try to access Runs sheet, create if doesn't exist
        try:
            runs_sheet = self._spreadsheet.worksheet(runs_sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create Runs sheet with header row
            runs_sheet = self._spreadsheet.add_worksheet(
                title=runs_sheet_name,
                rows=100,  # Start with 100 rows
                cols=4     # 4 columns: type, timestamp, records_added, records_updated
            )
            # Add header row
            header = ['type', 'timestamp', 'records_added', 'records_updated']
            runs_sheet.append_row(header)
            # Format header row (bold)
            runs_sheet.format('1:1', {'textFormat': {'bold': True}})

        # Append the run record
        runs_sheet.append_row(run_record)


def create_storage(output_path: Optional[str] = None, output_type: str = "auto") -> SLAStorage:
    """
    Factory function to create appropriate storage instance based on configuration

    Decision logic (in order):
    1. If output_path specified → Excel (implicit override)
    2. If output_type="excel" → Excel (explicit override)
    3. If Google Sheets configured → Google Sheets (default when configured)
    4. Otherwise → Excel (default fallback)

    Args:
        output_path: File path for Excel output (overrides Google Sheets if specified)
        output_type: Storage type ("auto", "excel", "sheets")

    Returns:
        SLAStorage instance (ExcelSLAStorage or GoogleSheetsSLAStorage)

    Raises:
        ValueError: If output_type is invalid
        ImportError: If Google Sheets requested but dependencies not installed
        Exception: If Google Sheets configured but authentication fails
    """
    # Validate output_type parameter
    if output_type not in ("auto", "excel", "sheets"):
        raise ValueError(
            f"Invalid output_type: {output_type}. "
            f"Must be 'auto', 'excel', or 'sheets'"
        )

    # Decision 1: If output_path specified, use Excel (implicit override)
    if output_path:
        return ExcelSLAStorage(output_path)

    # Decision 2: If output_type="excel", use Excel (explicit override)
    if output_type == "excel":
        # Use default path if not specified
        default_path = "files/sla_tracking.xlsx"
        return ExcelSLAStorage(default_path)

    # Decision 3: If output_type="sheets", require Google Sheets config
    if output_type == "sheets":
        google_config = config.get_google_sheets_config()
        if not google_config:
            raise ValueError(
                "output_type='sheets' specified but Google Sheets not configured. "
                "Please set GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, and "
                "GOOGLE_SHEET_NAME in env/.env file."
            )
        return GoogleSheetsSLAStorage(
            credentials_file=google_config['credentials_file'],
            sheet_id=google_config['sheet_id'],
            sheet_name=google_config['sheet_name']
        )

    # Decision 4: Auto-detect based on configuration
    # output_type="auto" - check if Google Sheets configured
    google_config = config.get_google_sheets_config()
    if google_config:
        # Google Sheets configured - use it
        return GoogleSheetsSLAStorage(
            credentials_file=google_config['credentials_file'],
            sheet_id=google_config['sheet_id'],
            sheet_name=google_config['sheet_name']
        )

    # Default fallback: Excel
    default_path = "files/sla_tracking.xlsx"
    return ExcelSLAStorage(default_path)
