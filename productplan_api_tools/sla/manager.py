"""
SLA Manager

Orchestration layer for SLA tracking commands.
Coordinates API fetching, business logic, and storage.
"""

import pandas as pd
from typing import Dict, Any, List, Tuple, Set
from collections import Counter
from datetime import datetime, timedelta

from productplan_api_tools.api.ideas import IdeasResource
from productplan_api_tools.api.teams import TeamsResource
from productplan_api_tools import utils, config
from productplan_api_tools.sla.calculator import (
    extract_idea_status,
    calculate_sla_columns,
    compare_timestamps
)
from productplan_api_tools.sla.storage import ExcelSLAStorage


# Configuration constants
SLA_UPDATE_LOOKBACK_DAYS = 14  # Number of days to look back when fetching updated ideas


def generate_idea_url(idea_id: int) -> str:
    """
    Generate URL for an idea using configured URL prefix

    Defensive handling of trailing slashes:
    - Strips trailing slash from prefix
    - Ensures single slash between prefix and ID

    Args:
        idea_id: The idea ID

    Returns:
        Full URL to the idea (e.g., "https://app.productplan.com/ideas/12345")

    Example:
        >>> generate_idea_url(12345)
        'https://app.productplan.com/ideas/12345'
    """
    url_prefix = config.get_url_prefix()
    # Defensive: strip trailing slash from prefix to avoid double slashes
    url_prefix = url_prefix.rstrip('/')
    return f"{url_prefix}/{idea_id}"


def apply_idea_filters(df: pd.DataFrame, verbose: bool = True) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Apply filtering rules to exclude test/development ideas

    Filtering rules (applied in order):
    1. Only include ideas created on or after Sep 15, 2025
    2. Exclude ideas created by "Jason Ladicos" before Nov 3, 2025
    3. Exclude ideas where customer is exactly "TEST"

    Args:
        df: DataFrame with ideas (must have created_at, source_name, customer columns)
        verbose: If True, print filtering statistics

    Returns:
        Tuple of (filtered_df, stats_dict) where stats_dict contains:
        - 'initial_count': Number of ideas before filtering
        - 'date_filtered': Ideas filtered by date cutoff
        - 'jason_filtered': Ideas filtered by Jason Ladicos rule
        - 'test_filtered': Ideas filtered by TEST customer rule
        - 'total_filtered': Total ideas removed
        - 'remaining': Ideas remaining after filtering
    """
    initial_count = len(df)
    stats = {'initial_count': initial_count}

    # Handle empty DataFrame - return immediately with zero stats
    if initial_count == 0:
        stats.update({
            'date_filtered': 0,
            'jason_filtered': 0,
            'test_filtered': 0,
            'total_filtered': 0,
            'remaining': 0
        })
        if verbose:
            print("\nNo ideas to filter (empty DataFrame)")
        return df, stats

    # Ensure created_at is datetime with timezone
    if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    elif df['created_at'].dt.tz is None:
        df['created_at'] = df['created_at'].dt.tz_localize('UTC')

    # Filter 1: Only include ideas created on or after Sep 15, 2025
    cutoff_date = pd.Timestamp('2025-09-15', tz='UTC')
    df = df[df['created_at'] >= cutoff_date].copy()
    stats['date_filtered'] = initial_count - len(df)

    # Filter 2: Exclude ideas created by Jason Ladicos before Nov 3, 2025
    jason_cutoff = pd.Timestamp('2025-11-03', tz='UTC')
    jason_filter = (df['source_name'] == 'Jason Ladicos') & (df['created_at'] < jason_cutoff)
    stats['jason_filtered'] = jason_filter.sum()
    df = df[~jason_filter].copy()

    # Filter 3: Exclude ideas where customer is exactly "TEST"
    test_filter = df['customer'] == 'TEST'
    stats['test_filtered'] = test_filter.sum()
    df = df[~test_filter].copy()

    stats['total_filtered'] = initial_count - len(df)
    stats['remaining'] = len(df)

    if verbose:
        print("\nApplying filtering rules...")
        print(f"  Filtered by date (before {cutoff_date.date()}): {stats['date_filtered']} ideas")
        print(f"  Filtered Jason Ladicos ideas before {jason_cutoff.date()}: {stats['jason_filtered']} ideas")
        print(f"  Filtered TEST customer ideas: {stats['test_filtered']} ideas")
        print(f"Total filtered: {stats['total_filtered']} ideas")
        print(f"Remaining ideas: {stats['remaining']}")

    return df, stats


def sla_init(output_path: str, token_file: str) -> None:
    """
    Initialize SLA tracking spreadsheet with all ideas

    Fetches all ideas from ProductPlan API, calculates SLA columns,
    and creates initial Excel spreadsheet for tracking.

    Args:
        output_path: Path to output Excel file
        token_file: Path to file containing API token

    Side effects:
        - Prints progress information
        - Creates Excel file at output_path
        - Creates parent directory if it doesn't exist

    Column ordering in output:
        id, name, description, customer, source_name, source_email,
        created_at, updated_at, idea_status, location_status,
        [team columns...],
        response_sla, roadmap_sla,
        currently_meets_response_sla, currently_meets_roadmap_sla
    """
    print("Initializing SLA tracking spreadsheet...")
    print(f"Output file: {output_path}")

    # Create API resources
    ideas_resource = IdeasResource(token_file)
    teams_resource = TeamsResource(token_file)

    # Fetch ALL ideas (including archived)
    print("\nFetching all ideas from ProductPlan API...")
    ideas_data = ideas_resource.fetch_enhanced(
        page=1,
        page_size=200,
        filters=None,
        get_all=True,
        location_status="all"  # Include archived ideas
    )
    print(f"Fetched {len(ideas_data)} ideas")

    # Build team mapping
    print("\nFetching teams...")
    team_mapping = teams_resource.build_id_to_name_mapping()
    print(f"Found {len(team_mapping)} teams")

    # Process ideas (add custom field columns and team columns)
    print("\nProcessing ideas...")
    processed_ideas = utils.process_ideas(ideas_data, team_mapping)

    # Add SLA columns to each idea
    print("\nCalculating SLA columns...")
    status_counts = Counter()
    for idea in processed_ideas:
        # Extract idea status from custom dropdown fields
        idea_status = extract_idea_status(idea)
        idea['idea_status'] = idea_status

        # Track status distribution
        status_counts[idea_status if idea_status else '(no status)'] += 1

        # Calculate SLA columns (no existing data for init)
        sla_columns = calculate_sla_columns(idea, existing_sla_data=None)

        # Add SLA columns to idea
        idea['response_sla'] = sla_columns['response_sla']
        idea['roadmap_sla'] = sla_columns['roadmap_sla']
        idea['currently_meets_response_sla'] = sla_columns['currently_meets_response_sla']
        idea['currently_meets_roadmap_sla'] = sla_columns['currently_meets_roadmap_sla']

    # Convert to DataFrame
    df = pd.DataFrame(processed_ideas)

    # Add URL column (immediately after id)
    if 'id' in df.columns and len(df) > 0:
        df['url'] = df['id'].apply(generate_idea_url)

    # Apply filtering rules to exclude test/development ideas
    df, filter_stats = apply_idea_filters(df, verbose=True)

    # Handle empty DataFrame case - create DataFrame with proper column structure
    if len(df) == 0:
        # Create empty DataFrame with correct column structure
        df = pd.DataFrame(columns=[
            'id', 'url', 'name', 'description', 'customer', 'source_name', 'source_email',
            'idea_status', 'created_at', 'updated_at', 'response_sla', 'roadmap_sla',
            'currently_meets_response_sla', 'currently_meets_roadmap_sla', 'location_status'
        ])
        # Write empty spreadsheet
        storage = ExcelSLAStorage(output_path)
        storage.write(df)
        print("\nNo ideas to track after filtering. Empty spreadsheet created.")
        print(f"Spreadsheet created: {output_path}")
        return

    # Remove timezone info from datetime columns for Excel compatibility
    # created_at is already tz-aware from filtering step
    df['created_at'] = df['created_at'].dt.tz_localize(None)

    # Convert other datetime columns and remove timezone
    if 'updated_at' in df.columns:
        df['updated_at'] = pd.to_datetime(df['updated_at'], utc=True, errors='coerce')
        if df['updated_at'].dt.tz is not None:
            df['updated_at'] = df['updated_at'].dt.tz_localize(None)

    # SLA columns might already be datetime objects from calculate_sla_columns()
    # Just ensure they're timezone-naive
    if 'response_sla' in df.columns:
        # If already datetime, just remove tz; if not, convert first
        if not pd.api.types.is_datetime64_any_dtype(df['response_sla']):
            df['response_sla'] = pd.to_datetime(df['response_sla'], utc=True, errors='coerce')
        if pd.api.types.is_datetime64_any_dtype(df['response_sla']) and df['response_sla'].dt.tz is not None:
            df['response_sla'] = df['response_sla'].dt.tz_localize(None)

    if 'roadmap_sla' in df.columns:
        # If already datetime, just remove tz; if not, convert first
        if not pd.api.types.is_datetime64_any_dtype(df['roadmap_sla']):
            df['roadmap_sla'] = pd.to_datetime(df['roadmap_sla'], utc=True, errors='coerce')
        if pd.api.types.is_datetime64_any_dtype(df['roadmap_sla']) and df['roadmap_sla'].dt.tz is not None:
            df['roadmap_sla'] = df['roadmap_sla'].dt.tz_localize(None)

    # Reorder columns to match specification
    # Core columns before created_at
    pre_date_columns = [
        'id', 'url', 'name', 'description', 'customer',
        'source_name', 'source_email', 'idea_status'
    ]

    # Date columns
    date_columns = ['created_at', 'updated_at']

    # SLA columns (immediately after updated_at)
    sla_columns_list = [
        'response_sla', 'roadmap_sla',
        'currently_meets_response_sla', 'currently_meets_roadmap_sla'
    ]

    # Location status
    status_columns = ['location_status']

    # Team columns (all teams from mapping, sorted by team ID)
    # Sort team_mapping items by ID (key), then extract team names (values)
    team_columns = [name for team_id, name in sorted(team_mapping.items(), key=lambda x: x[0])]

    # Custom field columns (everything else)
    all_ordered = pre_date_columns + date_columns + sla_columns_list + status_columns + team_columns
    custom_columns = [
        col for col in df.columns
        if col not in all_ordered
    ]

    # Final column order:
    # id, url, name, desc, customer, source_name, source_email, idea_status,
    # created_at, updated_at, [SLA columns], location_status, [custom fields], [team columns sorted by ID]
    column_order = pre_date_columns + date_columns + sla_columns_list + status_columns + custom_columns + team_columns

    # Only include columns that exist in the DataFrame
    column_order = [col for col in column_order if col in df.columns]

    # Reorder DataFrame
    df = df[column_order]

    # Write to Excel
    print(f"\nWriting to Excel: {output_path}")
    storage = ExcelSLAStorage(output_path)
    storage.write(df)

    # Print summary
    print("\n" + "="*60)
    print("SLA INITIALIZATION COMPLETE")
    print("="*60)
    print(f"Total ideas: {len(df)}")
    print(f"\nIdea status breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")

    # SLA compliance summary
    response_met = df['currently_meets_response_sla'].sum()
    roadmap_met = df['currently_meets_roadmap_sla'].sum()
    print(f"\nCurrent SLA compliance:")
    print(f"  Response SLA met: {response_met}/{len(df)} ({response_met/len(df)*100:.1f}%)")
    print(f"  Roadmap SLA met: {roadmap_met}/{len(df)} ({roadmap_met/len(df)*100:.1f}%)")

    print(f"\nSpreadsheet created: {output_path}")
    print("="*60)


def sla_update(output_path: str, token_file: str) -> None:
    """
    Update SLA tracking spreadsheet with recent changes

    Fetches ideas updated in the last 14 days, applies filtering rules,
    and updates the spreadsheet with changes. Preserves historical SLA dates
    while updating current status and compliance.

    Args:
        output_path: Path to existing SLA tracking Excel file
        token_file: Path to file containing API token

    Side effects:
        - Prints progress information
        - Updates Excel file at output_path
        - If spreadsheet doesn't exist, calls sla_init() instead

    Business Logic:
        - Fetches ideas with updated_at in last 14 days
        - Applies same filtering rules as sla_init()
        - Updates existing ideas if API timestamp is newer
        - Adds new ideas that pass filters (SLA dates = updated_at, compliance = created_at)
        - Removes ideas that now fail filters (opportunistic cleanup)
        - Preserves historical SLA dates when updating existing ideas
    """
    print("Updating SLA tracking spreadsheet...")
    print(f"Spreadsheet: {output_path}")

    # Check if spreadsheet exists
    storage = ExcelSLAStorage(output_path)
    if not storage.exists():
        print("\nSpreadsheet doesn't exist. Running initial setup...")
        sla_init(output_path, token_file)
        return

    # Calculate lookback date for API filter
    lookback_date = (datetime.now() - timedelta(days=SLA_UPDATE_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
    print(f"\nFetching ideas updated since: {lookback_date} ({SLA_UPDATE_LOOKBACK_DAYS}-day lookback)")

    # Create API resources
    ideas_resource = IdeasResource(token_file)
    teams_resource = TeamsResource(token_file)

    # Fetch ideas updated in lookback period
    print("\nFetching recently updated ideas from ProductPlan API...")
    fetched_ideas = ideas_resource.fetch_enhanced(
        page=1,
        page_size=200,
        filters={'updated_at_gteq': lookback_date},
        get_all=True,
        location_status="all"  # Include archived ideas
    )
    print(f"Fetched {len(fetched_ideas)} recently updated ideas")

    # Track which ideas were fetched (before filtering) for cleanup logic
    fetched_idea_ids: Set[int] = {idea['id'] for idea in fetched_ideas}

    # Build team mapping
    print("\nFetching teams...")
    team_mapping = teams_resource.build_id_to_name_mapping()
    print(f"Found {len(team_mapping)} teams")

    # Process fetched ideas (add custom field columns and team columns)
    print("\nProcessing fetched ideas...")
    processed_ideas = utils.process_ideas(fetched_ideas, team_mapping)

    # Add idea_status to each idea
    for idea in processed_ideas:
        idea['idea_status'] = extract_idea_status(idea)

    # Convert to DataFrame for filtering
    fetched_df = pd.DataFrame(processed_ideas)

    # Add URL column (immediately after id)
    if 'id' in fetched_df.columns and len(fetched_df) > 0:
        fetched_df['url'] = fetched_df['id'].apply(generate_idea_url)

    # Apply filtering rules to exclude test/development ideas
    filtered_df, filter_stats = apply_idea_filters(fetched_df, verbose=True)

    # Extract IDs from filtered DataFrame (handle empty case)
    filtered_idea_ids: Set[int] = set(filtered_df['id'].tolist()) if len(filtered_df) > 0 else set()

    print(f"\nAfter filtering: {len(filtered_df)} ideas to process")

    # Read existing spreadsheet
    print("\nReading existing spreadsheet...")
    existing_df = storage.read()
    print(f"Existing spreadsheet has {len(existing_df)} ideas")

    # Add URL column if missing (defensive - for old spreadsheets without URL column)
    if 'url' not in existing_df.columns and 'id' in existing_df.columns and len(existing_df) > 0:
        existing_df['url'] = existing_df['id'].apply(generate_idea_url)

    # Create lookup dict: idea_id → existing row (as dict)
    existing_lookup: Dict[int, Dict[str, Any]] = {}
    for idx, row in existing_df.iterrows():
        existing_lookup[row['id']] = row.to_dict()

    existing_idea_ids: Set[int] = set(existing_lookup.keys())

    # Track changes
    added_count = 0
    updated_count = 0
    skipped_count = 0
    removed_count = 0

    # Process each filtered idea
    print("\nProcessing changes...")

    for _, idea_row in filtered_df.iterrows():
        idea_id = idea_row['id']
        idea_dict = idea_row.to_dict()

        if idea_id in existing_lookup:
            # Idea exists in spreadsheet
            existing_idea = existing_lookup[idea_id]

            # Compare timestamps to see if API is newer
            api_updated_at = idea_dict.get('updated_at')
            spreadsheet_updated_at = existing_idea.get('updated_at')

            if compare_timestamps(api_updated_at, spreadsheet_updated_at):
                # Case 1: API is newer - Update existing row
                print(f"  Updating idea {idea_id}: {idea_dict.get('name', 'Unknown')[:50]}")

                # Get existing SLA data to preserve historical dates
                existing_sla_data = {
                    'response_sla': existing_idea.get('response_sla'),
                    'roadmap_sla': existing_idea.get('roadmap_sla')
                }

                # Calculate new SLA columns (preserves historical dates)
                sla_columns = calculate_sla_columns(idea_dict, existing_sla_data=existing_sla_data)

                # Update idea with new SLA columns
                idea_dict['response_sla'] = sla_columns['response_sla']
                idea_dict['roadmap_sla'] = sla_columns['roadmap_sla']
                idea_dict['currently_meets_response_sla'] = sla_columns['currently_meets_response_sla']
                idea_dict['currently_meets_roadmap_sla'] = sla_columns['currently_meets_roadmap_sla']

                # Update the row in existing_df
                # First, add any new columns that don't exist yet (e.g., new team columns or custom fields)
                for col in idea_dict.keys():
                    if col not in existing_df.columns:
                        # Add new column with 0 for team columns, NaN for others
                        if col in team_mapping.values():
                            existing_df[col] = 0
                        else:
                            existing_df[col] = pd.NA

                # Get the row index for this idea
                row_idx = existing_df[existing_df['id'] == idea_id].index[0]
                # Update each column value
                for col in idea_dict.keys():
                    existing_df.at[row_idx, col] = idea_dict[col]

                updated_count += 1
            else:
                # Case 3: API not newer - Skip
                skipped_count += 1
        else:
            # Case 2: Not in spreadsheet - Add as new idea
            print(f"  Adding new idea {idea_id}: {idea_dict.get('name', 'Unknown')[:50]}")

            # Calculate SLA columns (no existing data, uses updated_at for SLA dates)
            sla_columns = calculate_sla_columns(idea_dict, existing_sla_data=None)

            # Add SLA columns to idea
            idea_dict['response_sla'] = sla_columns['response_sla']
            idea_dict['roadmap_sla'] = sla_columns['roadmap_sla']
            idea_dict['currently_meets_response_sla'] = sla_columns['currently_meets_response_sla']
            idea_dict['currently_meets_roadmap_sla'] = sla_columns['currently_meets_roadmap_sla']

            # Add URL if not already present (should already be there from filtered_df)
            if 'url' not in idea_dict or pd.isna(idea_dict['url']):
                idea_dict['url'] = generate_idea_url(idea_id)

            # Add new row to DataFrame
            # Convert dict to DataFrame and concatenate
            new_row_df = pd.DataFrame([idea_dict])
            existing_df = pd.concat([existing_df, new_row_df], ignore_index=True)

            added_count += 1

    # Case 4: Remove ideas that were fetched but now fail filters
    # (Opportunistic cleanup - only for ideas we fetched in this run)
    ideas_to_remove = existing_idea_ids & fetched_idea_ids - filtered_idea_ids

    if ideas_to_remove:
        print(f"\nRemoving {len(ideas_to_remove)} ideas that now fail filters...")
        for idea_id in ideas_to_remove:
            idea_name = existing_lookup[idea_id].get('name', 'Unknown')
            print(f"  Removing idea {idea_id}: {idea_name[:50]}")
            existing_df = existing_df[existing_df['id'] != idea_id]
            removed_count += 1

    # Remove timezone info from datetime columns for Excel compatibility
    datetime_columns = ['created_at', 'updated_at', 'response_sla', 'roadmap_sla']
    for col in datetime_columns:
        if col in existing_df.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(existing_df[col]):
                existing_df[col] = pd.to_datetime(existing_df[col], utc=True, errors='coerce')

            # Remove timezone if present
            if pd.api.types.is_datetime64_any_dtype(existing_df[col]) and existing_df[col].dt.tz is not None:
                existing_df[col] = existing_df[col].dt.tz_localize(None)

    # Reorder columns to match specification (same as sla_init)
    pre_date_columns = [
        'id', 'url', 'name', 'description', 'customer',
        'source_name', 'source_email', 'idea_status'
    ]

    date_columns = ['created_at', 'updated_at']

    sla_columns_list = [
        'response_sla', 'roadmap_sla',
        'currently_meets_response_sla', 'currently_meets_roadmap_sla'
    ]

    status_columns = ['location_status']

    # Team columns (all teams from mapping, sorted by team ID)
    # Sort team_mapping items by ID (key), then extract team names (values)
    team_columns = [name for team_id, name in sorted(team_mapping.items(), key=lambda x: x[0])]

    # Custom field columns (everything else)
    all_ordered = pre_date_columns + date_columns + sla_columns_list + status_columns + team_columns
    custom_columns = [
        col for col in existing_df.columns
        if col not in all_ordered
    ]

    # Final column order:
    # id, url, name, desc, customer, source_name, source_email, idea_status,
    # created_at, updated_at, [SLA columns], location_status, [custom fields], [team columns sorted by ID]
    column_order = pre_date_columns + date_columns + sla_columns_list + status_columns + custom_columns + team_columns

    # Only include columns that exist in the DataFrame
    column_order = [col for col in column_order if col in existing_df.columns]

    # Reorder DataFrame
    existing_df = existing_df[column_order]

    # Write updated DataFrame
    print(f"\nWriting updates to: {output_path}")
    storage.write(existing_df)

    # Print summary
    print("\n" + "="*60)
    print("SLA UPDATE COMPLETE")
    print("="*60)
    print(f"Ideas fetched: {len(fetched_ideas)}")
    print(f"Ideas after filtering: {len(filtered_df)}")
    print(f"Changes:")
    print(f"  Added: {added_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Removed: {removed_count}")
    print(f"  Skipped (no changes): {skipped_count}")
    print(f"\nTotal ideas in spreadsheet: {len(existing_df)}")

    # SLA compliance summary
    response_met = existing_df['currently_meets_response_sla'].sum()
    roadmap_met = existing_df['currently_meets_roadmap_sla'].sum()
    print(f"\nCurrent SLA compliance:")
    print(f"  Response SLA met: {response_met}/{len(existing_df)} ({response_met/len(existing_df)*100:.1f}%)")
    print(f"  Roadmap SLA met: {roadmap_met}/{len(existing_df)} ({roadmap_met/len(existing_df)*100:.1f}%)")

    print("="*60)
