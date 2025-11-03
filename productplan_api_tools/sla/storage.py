"""
SLA Storage

Storage abstraction layer for SLA tracking data.
Provides interface and implementations for reading/writing SLA spreadsheets.
"""

import os
from typing import Protocol
import pandas as pd
from datetime import datetime


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
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='w') as writer:
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
