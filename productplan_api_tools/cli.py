"""
CLI Module

Command-line interface for ProductPlan API Tools.
Handles argument parsing and command routing.
"""

import sys
import os
import argparse
from typing import Optional

# Import API resources
from productplan_api_tools.api.ideas import IdeasResource
from productplan_api_tools.api.teams import TeamsResource
from productplan_api_tools.api.okrs import OKRsResource
from productplan_api_tools.api.idea_forms import IdeaFormsResource
from productplan_api_tools.api.objective_maps import ObjectiveMappingResource

# Import exporters and utils as modules (for proper test mocking)
from productplan_api_tools import exporters
from productplan_api_tools import utils

# Import SLA manager functions
from productplan_api_tools.sla.manager import sla_init, sla_update


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments

    Defines all CLI arguments and their defaults.
    Identical to current implementation for backward compatibility.

    Returns:
        Parsed arguments namespace

    Arguments:
        --endpoint: ideas, teams, idea-forms, okrs, objectivemap (default: ideas)
        --token-file: Token file path (default: token.txt)
        --page: Page number (default: 1)
        --page-size: Items per page (default: 200)
        --filter: Filter key-value pairs (repeatable)
        --output: Output filename (default: files/productplan_data.xlsx)
        --all-pages: Fetch all pages flag
        --location-status: Ideas filter (default: not_archived)
        --objective-status: Objectives filter (default: active)
        --output-format: excel, markdown, javascript (default: excel)
    """
    parser = argparse.ArgumentParser(
        description='ProductPlan API Tools - Fetch and export ProductPlan data'
    )

    parser.add_argument(
        '--endpoint',
        type=str,
        default='ideas',
        choices=['ideas', 'teams', 'idea-forms', 'okrs', 'objectivemap', 'sla-init', 'sla-update'],
        help='API endpoint to fetch from or SLA command to run (default: ideas)'
    )

    parser.add_argument(
        '--token-file',
        type=str,
        default='token.txt',
        help='Path to file containing ProductPlan API token (default: token.txt)'
    )

    parser.add_argument(
        '--page',
        type=int,
        default=1,
        help='Page number to fetch (default: 1)'
    )

    parser.add_argument(
        '--page-size',
        type=int,
        default=200,
        help='Number of items per page (default: 200, max: 500)'
    )

    parser.add_argument(
        '--filter',
        nargs=2,
        action='append',
        metavar=('KEY', 'VALUE'),
        help='Filter key-value pairs (can be used multiple times)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='files/productplan_data.xlsx',
        help='Output filename (default: files/productplan_data.xlsx)'
    )

    parser.add_argument(
        '--all-pages',
        action='store_true',
        help='Fetch all pages of results (default: False)'
    )

    parser.add_argument(
        '--location-status',
        type=str,
        default='not_archived',
        choices=['all', 'visible', 'hidden', 'archived', 'not_archived'],
        help='Filter ideas by location status (default: not_archived)'
    )

    parser.add_argument(
        '--objective-status',
        type=str,
        default='active',
        choices=['active', 'all'],
        help='Filter objectives by status (default: active)'
    )

    parser.add_argument(
        '--output-format',
        type=str,
        default='excel',
        choices=['excel', 'markdown', 'javascript'],
        help='Output format (default: excel)'
    )

    return parser.parse_args()


# Handler functions for each endpoint

def handle_ideas_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle ideas endpoint command

    Args:
        args: Parsed arguments
        token_file: Path to token file

    Side effects:
        Fetches ideas, processes with custom fields and teams, exports to Excel
    """
    print("Fetching ideas...")

    # Create resources
    ideas_resource = IdeasResource(token_file)
    teams_resource = TeamsResource(token_file)

    # Build filter dictionary
    filters = {}
    if args.filter:
        for key, value in args.filter:
            filters[key] = value

    # Fetch ideas
    ideas_data = ideas_resource.fetch_enhanced(
        page=args.page,
        page_size=args.page_size,
        filters=filters if filters else None,
        get_all=args.all_pages,
        location_status=args.location_status
    )

    # Build team mapping
    team_mapping = teams_resource.build_id_to_name_mapping()

    # Process ideas (add custom field columns and team columns)
    processed_ideas = utils.process_ideas(ideas_data, team_mapping)

    # Export to Excel
    exporters.excel.export(processed_ideas, args.output)


def handle_teams_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle teams endpoint command

    Args:
        args: Parsed arguments
        token_file: Path to token file

    Side effects:
        Fetches teams, exports to Excel
    """
    print("Fetching teams...")

    # Create resource
    teams_resource = TeamsResource(token_file)

    # Build filter dictionary
    filters = {}
    if args.filter:
        for key, value in args.filter:
            filters[key] = value

    # Fetch teams
    teams_response = teams_resource.fetch_list(
        page=args.page,
        page_size=args.page_size,
        filters=filters if filters else None,
        get_all=args.all_pages
    )

    # Extract results
    teams_data = teams_response.get('results', [])

    # Export to Excel
    exporters.excel.export(teams_data, args.output)


def handle_idea_forms_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle idea-forms endpoint command

    Args:
        args: Parsed arguments
        token_file: Path to token file

    Side effects:
        Fetches idea forms, processes with flattened custom fields, exports to Excel
    """
    print("Fetching idea forms...")

    # Create resource
    idea_forms_resource = IdeaFormsResource(token_file)

    # Build filter dictionary
    filters = {}
    if args.filter:
        for key, value in args.filter:
            filters[key] = value

    # Fetch idea forms
    forms_data = idea_forms_resource.fetch_enhanced(
        page=args.page,
        page_size=args.page_size,
        filters=filters if filters else None,
        get_all=args.all_pages
    )

    # Process idea forms (flatten custom fields)
    processed_forms = utils.process_idea_forms(forms_data)

    # Export to Excel
    exporters.excel.export(processed_forms, args.output)


def handle_okrs_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle okrs endpoint command

    Args:
        args: Parsed arguments
        token_file: Path to token file

    Side effects:
        Fetches OKRs with team mapping, exports to Excel or Markdown based on output_format
    """
    print("Fetching OKRs (objectives and key results)...")

    # Create resources
    okrs_resource = OKRsResource(token_file)
    teams_resource = TeamsResource(token_file)

    # Build team mapping
    team_mapping = teams_resource.build_id_to_name_mapping()

    # Build filter dictionary
    filters = {}
    if args.filter:
        for key, value in args.filter:
            filters[key] = value

    # Fetch OKRs
    okr_data = okrs_resource.fetch_enhanced(
        page=args.page,
        page_size=args.page_size,
        filters=filters if filters else None,
        get_all=args.all_pages,
        status_filter=args.objective_status,
        team_mapping=team_mapping
    )

    # Export based on format
    if args.output_format == 'markdown':
        exporters.markdown.export_okr(okr_data, args.output)
    else:  # excel (default)
        exporters.excel.export(okr_data, args.output)


def handle_objectivemap_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle objectivemap endpoint command

    Args:
        args: Parsed arguments
        token_file: Path to token file

    Side effects:
        Fetches objective mapping with team mapping, exports to Excel or JavaScript based on output_format
    """
    print("Fetching objective mapping data...")

    # Create resources
    mapping_resource = ObjectiveMappingResource(token_file)
    teams_resource = TeamsResource(token_file)

    # Build team mapping
    team_mapping = teams_resource.build_id_to_name_mapping()

    # Build filter dictionary
    filters = {}
    if args.filter:
        for key, value in args.filter:
            filters[key] = value

    # Fetch mapping data
    mapping_data = mapping_resource.fetch_mapping_data(
        page=args.page,
        page_size=args.page_size,
        filters=filters if filters else None,
        get_all=args.all_pages,
        status_filter=args.objective_status,
        team_mapping=team_mapping
    )

    # Export based on format
    if args.output_format == 'javascript':
        exporters.javascript.export_miro(mapping_data, args.output)
    else:  # excel (default)
        exporters.excel.export(mapping_data, args.output)


def handle_sla_init_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle sla-init command

    Creates initial SLA tracking spreadsheet with all current ideas.

    Args:
        args: Parsed arguments
        token_file: Path to token file (always 'token.txt')

    Side effects:
        Creates Excel spreadsheet at output path with SLA tracking data
    """
    # Use sla_tracking.xlsx as default if still using generic default
    output_path = args.output
    if output_path == 'files/productplan_data.xlsx':
        output_path = 'files/sla_tracking.xlsx'

    print(f"Initializing SLA tracking spreadsheet...")
    print(f"Output: {output_path}")

    # Call sla_init from manager
    sla_init(output_path=output_path, token_file=token_file)


def handle_sla_update_command(args: argparse.Namespace, token_file: str) -> None:
    """
    Handle sla-update command

    Updates existing SLA tracking spreadsheet with recent changes (14-day lookback).

    Args:
        args: Parsed arguments
        token_file: Path to token file (always 'token.txt')

    Side effects:
        Updates Excel spreadsheet at output path with recent SLA changes
    """
    # Use sla_tracking.xlsx as default if still using generic default
    output_path = args.output
    if output_path == 'files/productplan_data.xlsx':
        output_path = 'files/sla_tracking.xlsx'

    print(f"Updating SLA tracking spreadsheet...")
    print(f"Output: {output_path}")

    # Call sla_update from manager
    sla_update(output_path=output_path, token_file=token_file)


def route_command(args: argparse.Namespace) -> None:
    """
    Route CLI command to appropriate handler

    This is a lightweight dispatcher that:
    1. Validates token file exists
    2. Routes to appropriate handler function based on endpoint

    Args:
        args: Parsed command-line arguments

    Raises:
        SystemExit: If token file missing or endpoint unknown

    Side effects:
        Delegates to handler functions which fetch/process/export data
    """
    # For SLA commands, always use token.txt (ignore --token-file arg)
    if args.endpoint in ['sla-init', 'sla-update']:
        token_file = 'token.txt'
    else:
        token_file = args.token_file

    # Validate token file exists
    if not os.path.isfile(token_file):
        print(f"Error: Token file not found: {token_file}")
        print("Please create a token file with your ProductPlan API token.")
        sys.exit(1)

    # Route to appropriate handler
    handlers = {
        'ideas': handle_ideas_command,
        'teams': handle_teams_command,
        'idea-forms': handle_idea_forms_command,
        'okrs': handle_okrs_command,
        'objectivemap': handle_objectivemap_command,
        'sla-init': handle_sla_init_command,
        'sla-update': handle_sla_update_command
    }

    handler = handlers.get(args.endpoint)
    if handler is None:
        print(f"Error: Unknown endpoint: {args.endpoint}")
        print(f"Valid endpoints: {', '.join(handlers.keys())}")
        sys.exit(1)

    # Call the handler
    handler(args, token_file)
