"""
Utility Functions

Reusable parsing and processing functions for ProductPlan API data.
"""

import json
from typing import List, Dict, Any, Set


# Custom field parsing functions

def parse_custom_text_fields(custom_text_fields_data: Any) -> List[Dict[str, Any]]:
    """
    Parse custom text fields from various formats

    Handles both string (JSON) and list formats.

    Args:
        custom_text_fields_data: Raw custom text fields from API
                                 Can be: JSON string, list, or None

    Returns:
        List of field dictionaries with 'label' and 'value' keys
        Returns empty list if parsing fails or data is None

    Side effects:
        Prints warning if JSON parsing fails on non-empty string

    Example:
        Input: '[{"label": "Problem", "value": "Auth issue"}]'
        Output: [{"label": "Problem", "value": "Auth issue"}]
    """
    if custom_text_fields_data is None:
        return []

    # If it's already a list, return it
    if isinstance(custom_text_fields_data, list):
        return custom_text_fields_data

    # If it's a string, try to parse as JSON
    if isinstance(custom_text_fields_data, str):
        if not custom_text_fields_data.strip():
            return []

        try:
            parsed = json.loads(custom_text_fields_data)
            if isinstance(parsed, list):
                return parsed
            else:
                print(f"Warning: Parsed custom_text_fields is not a list: {type(parsed)}")
                return []
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse custom_text_fields JSON: {e}")
            return []

    # Unknown type
    return []


def parse_custom_dropdown_fields(custom_dropdown_fields_data: Any) -> List[Dict[str, Any]]:
    """
    Parse custom dropdown fields from API response

    Similar to parse_custom_text_fields but for dropdown fields.

    Args:
        custom_dropdown_fields_data: Raw custom dropdown fields from API

    Returns:
        List of field dictionaries with 'label' and 'value' keys
        Returns empty list if data is None or not a list
    """
    if custom_dropdown_fields_data is None:
        return []

    # Dropdown fields are typically already in list format
    if isinstance(custom_dropdown_fields_data, list):
        return custom_dropdown_fields_data

    # If not a list, return empty
    return []


def parse_team_ids(team_ids_data: Any) -> List[int]:
    """
    Parse team IDs from various formats

    Handles: list, comma-separated string, None

    Args:
        team_ids_data: Raw team IDs from API
                      Can be: list of ints, comma-separated string, or None

    Returns:
        List of team IDs as integers
        Returns empty list if parsing fails or data is None

    Side effects:
        Prints warning if string parsing fails

    Example:
        Input: "123, 456, 789"
        Output: [123, 456, 789]
    """
    if team_ids_data is None:
        return []

    # If it's already a list, return it
    if isinstance(team_ids_data, list):
        return team_ids_data

    # If it's a string, parse as comma-separated integers
    if isinstance(team_ids_data, str):
        if not team_ids_data.strip():
            return []

        try:
            # Split by comma and convert to integers
            team_ids = [int(tid.strip()) for tid in team_ids_data.split(',') if tid.strip()]
            return team_ids
        except (ValueError, AttributeError) as e:
            print(f"Warning: Failed to parse team_ids string: {e}")
            return []

    # Unknown type
    return []


# Field processing functions for ideas

def add_custom_field_columns(idea: Dict[str, Any], field_labels: Set[str]) -> Dict[str, Any]:
    """
    Add custom text field columns to an idea dictionary

    Creates columns like "Custom: Problem to be solved" for each field label.

    Args:
        idea: Original idea dictionary
        field_labels: Set of all possible custom field labels across all ideas

    Returns:
        Modified idea dictionary with custom field columns added
        All field labels get columns; values filled from idea's custom_text_fields

    Example:
        field_labels = {"Problem", "Solution"}
        idea with Problem="Auth" → adds "Custom: Problem"="Auth", "Custom: Solution"=""
    """
    # Parse the custom text fields from the idea
    custom_fields = parse_custom_text_fields(idea.get('custom_text_fields'))

    # Create a lookup dictionary for faster access
    field_values = {field['label']: field.get('value', '') for field in custom_fields}

    # Add a column for each field label
    for label in field_labels:
        column_name = f"Custom: {label}"
        idea[column_name] = field_values.get(label, '')

    return idea


def add_custom_dropdown_columns(idea: Dict[str, Any], field_labels: Set[str]) -> Dict[str, Any]:
    """
    Add custom dropdown field columns to an idea dictionary

    Creates columns like "Custom_Dropdown: Priority" for each field label.

    Args:
        idea: Original idea dictionary
        field_labels: Set of all possible custom dropdown field labels

    Returns:
        Modified idea dictionary with custom dropdown columns added
    """
    # Parse the custom dropdown fields from the idea
    custom_fields = parse_custom_dropdown_fields(idea.get('custom_dropdown_fields'))

    # Create a lookup dictionary for faster access
    field_values = {field['label']: field.get('value', '') for field in custom_fields}

    # Add a column for each field label
    for label in field_labels:
        column_name = f"Custom_Dropdown: {label}"
        idea[column_name] = field_values.get(label, '')

    return idea


def add_team_columns(idea: Dict[str, Any], team_mapping: Dict[int, str]) -> Dict[str, Any]:
    """
    Add team assignment columns to an idea dictionary

    Creates binary columns (1/0) for each team showing if idea is assigned to that team.

    Args:
        idea: Original idea dictionary
        team_mapping: Dictionary of team_id -> team_name

    Returns:
        Modified idea dictionary with team columns added

    Example:
        team_mapping = {1: "Engineering", 2: "Product"}
        idea with team_ids=[1] → adds "Engineering"=1, "Product"=0
    """
    # Parse team IDs from the idea
    team_ids = parse_team_ids(idea.get('team_ids'))

    # Add a column for each team
    for team_id, team_name in team_mapping.items():
        idea[team_name] = 1 if team_id in team_ids else 0

    return idea


# Composite processing functions

def process_ideas(ideas_data: List[Dict[str, Any]],
                 team_mapping: Dict[int, str]) -> List[Dict[str, Any]]:
    """
    Process ideas data: add custom field columns and team columns

    Two-pass algorithm:
    1. Collect all unique custom field labels (text and dropdown)
    2. Process each idea to add columns

    Args:
        ideas_data: List of enhanced idea dictionaries
        team_mapping: Dictionary of team_id -> team_name

    Returns:
        List of processed ideas with added columns:
        - Custom: <label> columns for text fields
        - Custom_Dropdown: <label> columns for dropdown fields
        - <team_name> columns for team assignments (1/0)

    Side effects:
        Prints progress information:
        - Number of unique field labels found
        - Processing status
    """
    if not ideas_data:
        return []

    print(f"Processing {len(ideas_data)} ideas...")

    # First pass: collect all unique custom field labels
    text_field_labels = set()
    dropdown_field_labels = set()

    for idea in ideas_data:
        # Collect custom text field labels
        custom_text_fields = parse_custom_text_fields(idea.get('custom_text_fields'))
        for field in custom_text_fields:
            if 'label' in field:
                text_field_labels.add(field['label'])

        # Collect custom dropdown field labels
        custom_dropdown_fields = parse_custom_dropdown_fields(idea.get('custom_dropdown_fields'))
        for field in custom_dropdown_fields:
            if 'label' in field:
                dropdown_field_labels.add(field['label'])

    print(f"Found {len(text_field_labels)} unique custom text field labels")
    print(f"Found {len(dropdown_field_labels)} unique custom dropdown field labels")

    # Second pass: process each idea
    processed_ideas = []
    for idea in ideas_data:
        # Create a copy to avoid modifying original
        processed_idea = idea.copy()

        # Add custom text field columns
        processed_idea = add_custom_field_columns(processed_idea, text_field_labels)

        # Add custom dropdown field columns
        processed_idea = add_custom_dropdown_columns(processed_idea, dropdown_field_labels)

        # Add team columns
        processed_idea = add_team_columns(processed_idea, team_mapping)

        processed_ideas.append(processed_idea)

    print(f"Successfully processed {len(processed_ideas)} ideas")
    return processed_ideas


def process_idea_forms(forms_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process idea forms data: flatten custom fields for Excel export

    Converts nested custom field structures to flat columns:
    - custom_text_fields[0].label → Custom_Text_Field_1_Label
    - custom_dropdown_fields[0].allowed_values → Custom_Dropdown_Field_1_Allowed_Values (comma-separated)

    Args:
        forms_data: List of enhanced form dictionaries

    Returns:
        List of processed forms with flattened custom field columns

    Side effects:
        Prints processing progress and count
        Removes original nested 'custom_text_fields' and 'custom_dropdown_fields' keys
    """
    if not forms_data:
        return []

    print(f"Processing {len(forms_data)} idea forms...")

    def _format_key(key: str) -> str:
        """
        Format field key for column name

        Rules:
        - Keys with underscores: convert snake_case to PascalCase (e.g., allowed_values → Allowed_Values)
        - "label" key: capitalize to "Label"
        - Other single-word keys: keep lowercase
        """
        if '_' in key:
            # Multi-word keys: convert to PascalCase
            parts = key.split('_')
            return '_'.join(part.capitalize() for part in parts)
        elif key == 'label':
            # Special case: "label" becomes "Label"
            return 'Label'
        else:
            # Single-word keys: keep lowercase
            return key

    processed_forms = []
    for form in forms_data:
        # Create a copy to avoid modifying original
        processed_form = form.copy()

        # Process custom text fields
        custom_text_fields = form.get('custom_text_fields', [])
        if custom_text_fields:
            for i, field in enumerate(custom_text_fields, 1):
                # Add each field attribute as a separate column
                for key, value in field.items():
                    # Format key for column name
                    formatted_key = _format_key(key)
                    column_name = f"Custom_Text_Field_{i}_{formatted_key}"
                    processed_form[column_name] = value

        # Process custom dropdown fields
        custom_dropdown_fields = form.get('custom_dropdown_fields', [])
        if custom_dropdown_fields:
            for i, field in enumerate(custom_dropdown_fields, 1):
                # Add each field attribute as a separate column
                for key, value in field.items():
                    # Format key for column name
                    formatted_key = _format_key(key)
                    column_name = f"Custom_Dropdown_Field_{i}_{formatted_key}"
                    # If it's a list (like allowed_values), join with comma
                    if isinstance(value, list):
                        processed_form[column_name] = ", ".join(str(v) for v in value)
                    else:
                        processed_form[column_name] = value

        # Remove original nested fields
        processed_form.pop('custom_text_fields', None)
        processed_form.pop('custom_dropdown_fields', None)

        processed_forms.append(processed_form)

    print(f"Successfully processed {len(processed_forms)} idea forms")
    return processed_forms
