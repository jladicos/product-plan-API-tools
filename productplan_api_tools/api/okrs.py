"""
OKRs Resource

Handles objectives and key results with team resolution and flattening.
"""

from typing import Dict, List, Any, Optional
from productplan_api_tools.api.client import BaseResource


class OKRsResource(BaseResource):
    """
    Resource for ProductPlan objectives and key results API

    Provides:
    - Objectives list/details fetching
    - Key results fetching per objective
    - Enhanced OKR data with team name resolution
    - Flattened format for export (one row per key result)
    """

    @property
    def endpoint_path(self) -> str:
        """Returns: "strategy/objectives" """
        return "strategy/objectives"

    def get_objectives(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
        """
        Get objectives from the ProductPlan API strategy endpoint

        Args:
            page: Page number to fetch (default: 1)
            page_size: Number of items per page (default: 200, max: 500)
            filters: Dictionary of filter key-value pairs to apply
            get_all: If True, fetches all pages of results

        Returns:
            API response containing objectives data with 'results' key
        """
        return self.fetch_list(page, page_size, filters, get_all)

    def get_objective_details(self, objective_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific objective by ID

        Args:
            objective_id: The unique ID of the objective to fetch

        Returns:
            Detailed objective data including team assignments, status, timestamps, etc.
        """
        return self.fetch_details(objective_id)

    def fetch_key_results(self, objective_id: int, page: int = 1, page_size: int = 200,
                         filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
        """
        Fetch key results for a specific objective

        Args:
            objective_id: The ID of the objective to fetch key results for
            page: Page number (default: 1)
            page_size: Items per page (default: 200)
            filters: Optional API filters
            get_all: Fetch all pages (default: False)

        Returns:
            API response with 'results' key containing key results

        Side effects:
            Prints progress information
        """
        endpoint = f"strategy/objectives/{objective_id}/key_results"
        if get_all:
            return self._fetch_all_pages(endpoint, page_size, filters)
        else:
            params = {
                "page": page,
                "page_size": page_size
            }

            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    params[f"q[{key}]"] = value

            return self._make_request(endpoint, params)

    def fetch_enhanced(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None,
                      get_all: bool = False,
                      status_filter: str = "active",
                      team_mapping: Optional[Dict[int, str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch objectives with key results in flattened format

        This method:
        1. Fetches list of objectives
        2. Filters by status (active vs all)
        3. For each objective, fetches details and key results
        4. Resolves team IDs to names using team_mapping
        5. Flattens to one row per key result (or one row if no key results)

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 200)
            filters: Optional API filters
            get_all: Fetch all pages (default: False)
            status_filter: "active" or "all" (default: "active")
            team_mapping: Optional dict of team_id -> team_name for resolution
                         If None, fetches teams internally (one API call)

        Returns:
            List of flattened OKR row dictionaries with structure:
            {
                'status': objective location_status,
                'team_name': resolved team name(s),
                'objective_name': objective name,
                'objective_description': objective description,
                'key_result_name': key result description,
                'key_result_target': target value,
                'key_result_current': current value,
                'key_result_progress': progress metric,
                'objective_id': objective ID,
                'key_result_id': key result ID
            }

        Side effects:
            Prints progress and team mapping information

        Note:
            - If objective has key results: one row per key result
            - If objective has no key results: one row with empty key result fields
            - Team names resolved from key result team_ids first, then objective team_ids
        """
        # Apply status filtering if needed
        if filters is None:
            filters = {}

        if status_filter == "active":
            # Try different possible field names for objective status
            filters["location_status"] = "active"
            print("Filtering for active objectives only (using location_status filter)")
        elif status_filter == "all":
            print("Getting all objectives regardless of status")

        print(f"Applying filters: {filters}")

        print("Fetching objectives...")
        objectives_response = self.get_objectives(page, page_size, filters, get_all)

        if 'results' not in objectives_response:
            print("No results found in objectives response")
            return []

        objectives = objectives_response['results']

        # If we're filtering for active objectives, also filter the results after fetching
        # This ensures we get the right filtering regardless of API filter field names
        if status_filter == "active":
            original_count = len(objectives)
            # Filter objectives based on common status field names
            objectives = [obj for obj in objectives if
                obj.get('location_status') == 'active' or
                obj.get('status') == 'active' or
                obj.get('state') == 'active' or
                (obj.get('location_status') != 'archived' and
                 obj.get('location_status') != 'inactive' and
                 obj.get('status') != 'archived' and
                 obj.get('status') != 'inactive' and
                 obj.get('state') != 'archived' and
                 obj.get('state') != 'inactive')]
            print(f"Filtered objectives from {original_count} to {len(objectives)} active objectives")

        okr_rows = []

        # Get team mapping if not provided
        if team_mapping is None:
            print("No team mapping provided, fetching teams internally...")
            teams_response = self._make_request("teams", {"page_size": 500, "page": 1})
            team_mapping = {}
            if 'results' in teams_response:
                for team in teams_response['results']:
                    if 'id' in team and 'name' in team:
                        team_mapping[team['id']] = team['name']

        print(f"Team mapping loaded: {len(team_mapping)} teams")
        if team_mapping:
            print(f"Sample teams: {list(team_mapping.items())[:3]}")  # Show first 3 teams

        print(f"Processing {len(objectives)} objectives and their key results...")

        for i, objective in enumerate(objectives, 1):
            if 'id' not in objective:
                print(f"Warning: Objective {i} has no ID, skipping")
                continue

            try:
                objective_id = objective['id']
                print(f"Processing objective {i}/{len(objectives)}: ID {objective_id}")

                # Get detailed objective information
                detailed_objective = self.get_objective_details(objective_id)
                enhanced_objective = {**objective, **detailed_objective}

                # Debug: show team data and status fields in objective
                obj_team_ids = enhanced_objective.get('team_ids', []) or enhanced_objective.get('team_id', [])
                print(f"  Objective {objective_id} team data: team_ids={enhanced_objective.get('team_ids')}, team_id={enhanced_objective.get('team_id')}")
                print(f"  Objective {objective_id} status data: status={enhanced_objective.get('status')}, location_status={enhanced_objective.get('location_status')}, state={enhanced_objective.get('state')}")

                # Apply status filtering based on detailed information
                if status_filter == "active":
                    obj_location_status = enhanced_objective.get('location_status', '')
                    if obj_location_status in ['archived', 'inactive']:
                        print(f"  Skipping objective {objective_id} with location_status={obj_location_status}")
                        continue

                # Get key results for this objective
                key_results_response = self.fetch_key_results(objective_id, get_all=True)

                if 'results' in key_results_response and key_results_response['results']:
                    key_results = key_results_response['results']
                    print(f"Found {len(key_results)} key results for objective {objective_id}")

                    # Create one row per key result
                    for kr in key_results:
                        # Debug: show key result fields
                        kr_id = kr.get('id', 'unknown')
                        print(f"    Key result {kr_id} fields: name='{kr.get('name')}', description='{kr.get('description')}', target='{kr.get('target')}', current='{kr.get('current')}'")

                        # Try to get team name from key result first, then fall back to objective
                        kr_team_ids = kr.get('team_ids', []) or kr.get('team_id', [])
                        obj_team_ids = enhanced_objective.get('team_ids', []) or enhanced_objective.get('team_id', [])

                        # Convert single team_id to list if needed
                        if isinstance(kr_team_ids, (int, str)) and kr_team_ids:
                            kr_team_ids = [kr_team_ids]
                        if isinstance(obj_team_ids, (int, str)) and obj_team_ids:
                            obj_team_ids = [obj_team_ids]

                        # Get team names - prefer key result teams, fall back to objective teams
                        team_ids = kr_team_ids if kr_team_ids else obj_team_ids
                        team_names = []
                        if team_ids:
                            for team_id in team_ids:
                                if team_id in team_mapping:
                                    team_names.append(team_mapping[team_id])

                        team_name = ', '.join(team_names) if team_names else ''

                        # Debug output
                        if not team_name and (kr_team_ids or obj_team_ids):
                            print(f"Warning: No team names found for objective {enhanced_objective.get('id')}, key result {kr.get('id')}")
                            print(f"  KR team_ids: {kr_team_ids}, Obj team_ids: {obj_team_ids}")
                            print(f"  Available teams in mapping: {list(team_mapping.keys())[:5]}...")  # Show first 5

                        row = {
                            'status': enhanced_objective.get('location_status', ''),
                            'team_name': team_name,
                            'objective_name': enhanced_objective.get('name', ''),
                            'objective_description': enhanced_objective.get('description', ''),
                            'key_result_name': kr.get('description', '') or kr.get('name', ''),
                            'key_result_target': kr.get('target', ''),
                            'key_result_current': kr.get('current', ''),
                            'key_result_progress': kr.get('progress', ''),
                            'objective_id': enhanced_objective.get('id', ''),
                            'key_result_id': kr.get('id', '')
                        }
                        okr_rows.append(row)
                else:
                    # No key results - create one row for the objective
                    print(f"No key results found for objective {objective_id}")
                    obj_team_ids = enhanced_objective.get('team_ids', []) or enhanced_objective.get('team_id', [])

                    # Convert single team_id to list if needed
                    if isinstance(obj_team_ids, (int, str)) and obj_team_ids:
                        obj_team_ids = [obj_team_ids]

                    # Get team names
                    team_names = []
                    if obj_team_ids:
                        for team_id in obj_team_ids:
                            if team_id in team_mapping:
                                team_names.append(team_mapping[team_id])

                    team_name = ', '.join(team_names) if team_names else ''

                    # Debug output
                    if not team_name and obj_team_ids:
                        print(f"Warning: No team names found for objective {objective_id}")
                        print(f"  Obj team_ids: {obj_team_ids}")
                        print(f"  Available teams in mapping: {list(team_mapping.keys())[:5]}...")  # Show first 5

                    row = {
                        'status': enhanced_objective.get('location_status', ''),
                        'team_name': team_name,
                        'objective_name': enhanced_objective.get('name', ''),
                        'objective_description': enhanced_objective.get('description', ''),
                        'key_result_name': '',
                        'key_result_target': '',
                        'key_result_current': '',
                        'key_result_progress': '',
                        'objective_id': enhanced_objective.get('id', ''),
                        'key_result_id': ''
                    }
                    okr_rows.append(row)

            except Exception as e:
                print(f"Warning: Failed to process objective ID {objective.get('id', 'unknown')}: {e}")
                # Create a basic row with available data
                obj_team_ids = objective.get('team_ids', []) or objective.get('team_id', [])

                # Convert single team_id to list if needed
                if isinstance(obj_team_ids, (int, str)) and obj_team_ids:
                    obj_team_ids = [obj_team_ids]

                # Get team names
                team_names = []
                if obj_team_ids:
                    for team_id in obj_team_ids:
                        if team_id in team_mapping:
                            team_names.append(team_mapping[team_id])

                team_name = ', '.join(team_names) if team_names else ''

                row = {
                    'status': objective.get('location_status', ''),
                    'team_name': team_name,
                    'objective_name': objective.get('name', ''),
                    'objective_description': objective.get('description', ''),
                    'key_result_name': '',
                    'key_result_target': '',
                    'key_result_current': '',
                    'key_result_progress': '',
                    'objective_id': objective.get('id', ''),
                    'key_result_id': ''
                }
                okr_rows.append(row)

        print(f"Successfully processed objectives and key results. Total rows: {len(okr_rows)}")
        return okr_rows
