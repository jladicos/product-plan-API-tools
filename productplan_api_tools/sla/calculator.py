"""
SLA Calculator

Pure business logic for calculating SLA compliance metrics.
Functions in this module are stateless and have no I/O dependencies.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd


def extract_idea_status(idea: Dict[str, Any]) -> str:
    """
    Extract the idea status from custom dropdown fields

    Searches for the "idea status" custom dropdown field and returns its value.

    Args:
        idea: Idea dictionary containing custom_dropdown_fields

    Returns:
        The idea status value (e.g., "On deck", "Accepted", "Rejected")
        Returns empty string if not found

    Example:
        >>> idea = {
        ...     'custom_dropdown_fields': [
        ...         {'label': 'idea status', 'value': 'Accepted'}
        ...     ]
        ... }
        >>> extract_idea_status(idea)
        'Accepted'
    """
    # Get custom dropdown fields from idea
    custom_dropdown_fields = idea.get('custom_dropdown_fields', [])

    # Handle case where it's not a list
    if not isinstance(custom_dropdown_fields, list):
        return ''

    # Search for "idea status" field (case-insensitive match)
    for field in custom_dropdown_fields:
        if isinstance(field, dict):
            label = field.get('label', '')
            if label.lower() == 'idea status':
                value = field.get('value', '')
                # Handle explicit None value - return empty string
                return value if value is not None else ''

    # Not found
    return ''


def calculate_sla_columns(
    idea: Dict[str, Any],
    existing_sla_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate SLA columns for an idea

    Calculates both historical SLA dates and current state booleans:
    - response_sla: Date when status first changed from "On deck" (set once, never cleared)
                    Uses updated_at timestamp for historical accuracy (falls back to current time)
    - roadmap_sla: Date when status first became "Accepted" or "Rejected" (set once, never cleared)
                   Uses updated_at timestamp for historical accuracy (falls back to current time)
    - currently_meets_response_sla: True if status changed within 14 days AND status is currently valid
    - currently_meets_roadmap_sla: True if status reached Accepted/Rejected within 60 days AND status is currently valid

    Args:
        idea: Idea dictionary with custom_dropdown_fields, created_at, updated_at, etc.
        existing_sla_data: Optional dict with existing response_sla and roadmap_sla dates
                          Used to preserve historical dates during updates

    Returns:
        Dictionary with four SLA columns:
        {
            'response_sla': datetime or None,
            'roadmap_sla': datetime or None,
            'currently_meets_response_sla': bool,
            'currently_meets_roadmap_sla': bool
        }

    Note:
        When setting SLA dates, prefers idea['updated_at'] over current time for historical accuracy.
        This assumes the status was changed at the last update time. Falls back to current time if
        updated_at is not available.

    Example:
        >>> idea = {
        ...     'custom_dropdown_fields': [{'label': 'idea status', 'value': 'Accepted'}],
        ...     'created_at': '2024-01-01T00:00:00Z',
        ...     'updated_at': '2024-01-05T00:00:00Z'
        ... }
        >>> result = calculate_sla_columns(idea)
        >>> result['response_sla']  # Will be set to updated_at (2024-01-05)
        >>> result['currently_meets_response_sla']
        True
        >>> result['currently_meets_roadmap_sla']
        True
    """
    # Extract current idea status
    idea_status = extract_idea_status(idea)

    # Parse created_at timestamp
    created_at = None
    if 'created_at' in idea and idea['created_at']:
        try:
            # Handle both string (ISO format) and datetime/Timestamp objects
            if isinstance(idea['created_at'], (datetime, pd.Timestamp)):
                created_at = idea['created_at']
                # Convert pandas Timestamp to datetime if needed
                if hasattr(created_at, 'to_pydatetime'):
                    created_at = created_at.to_pydatetime()
            else:
                # It's a string, parse it
                created_at_str = idea['created_at'].replace('Z', '+00:00')
                created_at = datetime.fromisoformat(created_at_str)
        except (ValueError, AttributeError, TypeError):
            # If parsing fails, we can't calculate time-based compliance
            pass

    # Parse updated_at timestamp - prefer this over "now" for historical accuracy
    updated_at = None
    if 'updated_at' in idea and idea['updated_at']:
        try:
            # Handle both string (ISO format) and datetime/Timestamp objects
            if isinstance(idea['updated_at'], (datetime, pd.Timestamp)):
                updated_at = idea['updated_at']
                # Convert pandas Timestamp to datetime if needed
                if hasattr(updated_at, 'to_pydatetime'):
                    updated_at = updated_at.to_pydatetime()
            else:
                # It's a string, parse it
                updated_at_str = idea['updated_at'].replace('Z', '+00:00')
                updated_at = datetime.fromisoformat(updated_at_str)
        except (ValueError, AttributeError, TypeError):
            pass

    # Initialize with existing SLA data if provided
    response_sla = existing_sla_data.get('response_sla') if existing_sla_data else None
    roadmap_sla = existing_sla_data.get('roadmap_sla') if existing_sla_data else None

    # Handle pandas NaT (Not a Time) - treat as None
    if response_sla is not None and pd.isna(response_sla):
        response_sla = None
    if roadmap_sla is not None and pd.isna(roadmap_sla):
        roadmap_sla = None

    # Determine timestamp to use for setting new SLA dates
    # Prefer updated_at (when status was likely changed) over "now" (for historical accuracy)
    # Fall back to "now" if updated_at is not available
    sla_date = updated_at if updated_at else datetime.utcnow()

    # Calculate response_sla: set once when status first moves off "On deck"
    # Only set if not already set and current status is not "On deck" and is not empty
    # Use updated_at for historical accuracy (when status was likely changed)
    if response_sla is None and idea_status and idea_status != "On deck":
        response_sla = sla_date

    # Calculate roadmap_sla: set once when status becomes "Accepted" or "Rejected"
    # Only set if not already set and current status is one of these
    # Use updated_at for historical accuracy (when status was likely changed)
    if roadmap_sla is None and idea_status in ["Accepted", "Rejected"]:
        roadmap_sla = sla_date

    # Calculate currently_meets_response_sla:
    # - response_sla must not be null (they responded)
    # - Status must currently be valid (not null/empty and not "On deck")
    # - Response must have occurred within 14 days of creation
    currently_meets_response_sla = False
    if response_sla is not None and idea_status and idea_status != "On deck" and created_at:
        # Check if response was within 14 days
        # Make response_sla timezone-aware if needed
        if response_sla.tzinfo is None:
            response_sla_aware = response_sla.replace(tzinfo=created_at.tzinfo)
        else:
            response_sla_aware = response_sla

        days_to_respond = (response_sla_aware - created_at).days
        currently_meets_response_sla = days_to_respond <= 14

    # Calculate currently_meets_roadmap_sla:
    # - roadmap_sla must not be null (they reached decision)
    # - Status must currently be "Accepted" or "Rejected"
    # - Decision must have occurred within 60 days of creation
    currently_meets_roadmap_sla = False
    if roadmap_sla is not None and idea_status in ["Accepted", "Rejected"] and created_at:
        # Check if decision was within 60 days
        # Make roadmap_sla timezone-aware if needed
        if roadmap_sla.tzinfo is None:
            roadmap_sla_aware = roadmap_sla.replace(tzinfo=created_at.tzinfo)
        else:
            roadmap_sla_aware = roadmap_sla

        days_to_decide = (roadmap_sla_aware - created_at).days
        currently_meets_roadmap_sla = days_to_decide <= 60

    return {
        'response_sla': response_sla,
        'roadmap_sla': roadmap_sla,
        'currently_meets_response_sla': currently_meets_response_sla,
        'currently_meets_roadmap_sla': currently_meets_roadmap_sla
    }


def compare_timestamps(api_updated_at: str, spreadsheet_updated_at: str) -> bool:
    """
    Compare two timestamps to determine if API data is newer

    Args:
        api_updated_at: Timestamp from API (ISO format string or datetime/Timestamp object)
        spreadsheet_updated_at: Timestamp from spreadsheet (ISO format string or datetime/Timestamp object)

    Returns:
        True if API timestamp is newer than spreadsheet timestamp
        False if spreadsheet is newer or equal, or if comparison fails

    Example:
        >>> compare_timestamps('2024-01-15T10:00:00Z', '2024-01-14T10:00:00Z')
        True
        >>> compare_timestamps('2024-01-14T10:00:00Z', '2024-01-15T10:00:00Z')
        False
    """
    # Handle missing or empty API timestamp
    if api_updated_at is None or (isinstance(api_updated_at, str) and not api_updated_at):
        return False

    # Handle missing or empty spreadsheet timestamp - API is newer if it exists
    if spreadsheet_updated_at is None or (isinstance(spreadsheet_updated_at, str) and not spreadsheet_updated_at):
        return True

    try:
        # Parse/convert API timestamp
        if isinstance(api_updated_at, (datetime, pd.Timestamp)):
            api_ts = api_updated_at
            # Convert pandas Timestamp to datetime if needed
            if hasattr(api_ts, 'to_pydatetime'):
                api_ts = api_ts.to_pydatetime()
        else:
            # It's a string, parse it
            api_ts_str = api_updated_at.replace('Z', '+00:00')
            api_ts = datetime.fromisoformat(api_ts_str)

        # Parse/convert spreadsheet timestamp
        if isinstance(spreadsheet_updated_at, (datetime, pd.Timestamp)):
            sheet_ts = spreadsheet_updated_at
            # Convert pandas Timestamp to datetime if needed
            if hasattr(sheet_ts, 'to_pydatetime'):
                sheet_ts = sheet_ts.to_pydatetime()
        else:
            # It's a string, parse it
            sheet_ts_str = spreadsheet_updated_at.replace('Z', '+00:00')
            sheet_ts = datetime.fromisoformat(sheet_ts_str)

        # Normalize both to timezone-naive for comparison (in case one has tz and other doesn't)
        if api_ts.tzinfo is not None:
            api_ts = api_ts.replace(tzinfo=None)
        if sheet_ts.tzinfo is not None:
            sheet_ts = sheet_ts.replace(tzinfo=None)

        # Compare timestamps - return True if API is newer
        return api_ts > sheet_ts

    except (ValueError, AttributeError, TypeError):
        # If parsing fails, return False (don't update)
        return False
