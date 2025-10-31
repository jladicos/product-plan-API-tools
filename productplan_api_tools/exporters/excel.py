"""
Excel Exporter

Exports data to Excel format using pandas.
"""

import os
from typing import List, Dict, Any
import pandas as pd
from productplan_api_tools.exporters import base


def export(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Export data to Excel file

    Args:
        data: List of dictionaries to export (each dict becomes a row)
        filename: Output filename (e.g., "files/output.xlsx")

    Raises:
        Exception: If export fails (pandas or file system errors)

    Side effects:
        Creates output directory if needed (via ensure_output_directory)
        Writes Excel file to disk
        Prints success message with absolute path
        Prints warning if data is empty

    Note:
        Uses pandas DataFrame.to_excel() with index=False
    """
    if not data:
        print("Warning: No data to export")
        return

    print(f"Exporting {len(data)} records to {filename}")
    try:
        # Create parent directory if it doesn't exist
        base.ensure_output_directory(filename)

        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        # Get full path to the output file
        abs_path = os.path.abspath(filename)
        print(f"Data successfully exported to {abs_path}")
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        raise
