"""
Markdown Exporter

Exports OKR data to structured Markdown format.
"""

import os
from typing import List, Dict, Any
from productplan_api_tools.exporters import base


def export_okr(okr_data: List[Dict[str, Any]], filename: str) -> None:
    """
    Export OKR data to Markdown file

    Takes flattened OKR data and reconstructs hierarchical structure:
    - Groups rows by objective_id
    - Creates H2 heading per objective
    - Lists key results as bullets

    Markdown structure:
    ```
    # Objectives and Key Results

    ## Objective Name
    Description text

    ### Team
    Team Name

    ### Key Results
    - Key result description (target: X) - Current: Y | Progress: Z%

    ## Another Objective
    ...
    ```

    Args:
        okr_data: List of flattened OKR dictionaries from OKRsResource.fetch_enhanced()
        filename: Output filename (e.g., "files/okrs.md")

    Raises:
        Exception: If file writing fails

    Side effects:
        Creates output directory if needed (via ensure_output_directory)
        Writes Markdown file to disk
        Prints success message with objective count
        Prints warning if data is empty

    Note:
        - Target values appear in parentheses: (target: 100%)
        - Objectives without key results show "No key results"
        - Team section only appears if team_name is present
    """
    if not okr_data:
        print("Warning: No OKR data to export")
        return

    print(f"Exporting OKR data to markdown format: {filename}")

    # Group data by objectives
    objectives = {}
    for row in okr_data:
        obj_id = row.get('objective_id', '')
        obj_name = row.get('objective_name', 'Unknown Objective')
        obj_description = row.get('objective_description', '')

        if obj_id not in objectives:
            objectives[obj_id] = {
                'name': obj_name,
                'description': obj_description,
                'team_name': row.get('team_name', ''),
                'status': row.get('status', ''),
                'key_results': []
            }

        # Add key result if it exists
        kr_name = row.get('key_result_name', '').strip()
        if kr_name:
            kr_data = {
                'name': kr_name,
                'target': row.get('key_result_target', ''),
                'current': row.get('key_result_current', ''),
                'progress': row.get('key_result_progress', '')
            }
            objectives[obj_id]['key_results'].append(kr_data)

    # Generate markdown content
    markdown_lines = []
    markdown_lines.append("# Objectives and Key Results")
    markdown_lines.append("")

    for obj_id, obj_data in objectives.items():
        # Objective heading (without team name)
        markdown_lines.append(f"## {obj_data['name']}")

        # Objective description
        if obj_data['description']:
            markdown_lines.append(obj_data['description'])
            markdown_lines.append("")

        # Team section
        if obj_data['team_name']:
            markdown_lines.append("### Team")
            markdown_lines.append(obj_data['team_name'])
            markdown_lines.append("")

        # Key results section
        markdown_lines.append("### Key Results")

        if obj_data['key_results']:
            for kr in obj_data['key_results']:
                kr_line = f"- {kr['name']}"

                # Add target in parentheses if available
                if kr['target']:
                    kr_line += f" (target: {kr['target']})"

                # Add other details after the target
                details = []
                if kr['current']:
                    details.append(f"Current: {kr['current']}")
                if kr['progress']:
                    details.append(f"Progress: {kr['progress']}")

                if details:
                    kr_line += f" - {' | '.join(details)}"

                markdown_lines.append(kr_line)
            markdown_lines.append("")
        else:
            markdown_lines.append("No key results")
            markdown_lines.append("")

    # Write to file
    try:
        # Create parent directory if it doesn't exist
        base.ensure_output_directory(filename)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))

        abs_path = os.path.abspath(filename)
        print(f"OKR data successfully exported to {abs_path}")
        print(f"Generated markdown for {len(objectives)} objectives")
    except Exception as e:
        print(f"Error exporting to markdown: {e}")
        raise
