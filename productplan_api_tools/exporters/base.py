"""
Base Exporter Utilities

Common utility functions for all exporters.
"""

import os


def ensure_output_directory(filename: str) -> None:
    """
    Ensure the output directory exists for a given filename

    Extracts directory path from filename and creates it if needed.
    Safe to call even if directory already exists.

    Args:
        filename: Full path to output file

    Side effects:
        Creates directory structure if it doesn't exist
        Prints directory creation message

    Example:
        ensure_output_directory("files/subdir/output.xlsx")
        Creates: files/subdir/ (if needed)
    """
    output_dir = os.path.dirname(filename)
    if output_dir:  # Only create if there's a directory component
        os.makedirs(output_dir, exist_ok=True)
        print(f"Ensuring output directory exists: {output_dir}")
