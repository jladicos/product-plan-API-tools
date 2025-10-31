"""
Objective Mapping Resource

Creates Cartesian product mapping between company and team objectives.
"""

from typing import Dict, List, Any, Optional
from productplan_api_tools.api.client import BaseResource


class ObjectiveMappingResource(BaseResource):
    """
    Resource for creating objective relationship mappings

    ProductPlan doesn't expose parent-child relationships between objectives,
    so this creates a Cartesian product of company objectives (no team_ids)
    and team objectives (with team_ids) for manual relationship configuration.
    """

    @property
    def endpoint_path(self) -> str:
        """Returns: "strategy/objectives" (same as OKRs) """
        return "strategy/objectives"

    def get_objectives(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
        """
        Get objectives from the ProductPlan API strategy endpoint

        Args:
            page: Page number
            page_size: Items per page
            filters: Optional filters
            get_all: Fetch all pages

        Returns:
            API response with objectives data
        """
        return self.fetch_list(page, page_size, filters, get_all)

    def fetch_mapping_data(self, page: int = 1, page_size: int = 200,
                          filters: Optional[Dict[str, Any]] = None,
                          get_all: bool = False,
                          status_filter: str = "active",
                          team_mapping: Optional[Dict[int, str]] = None) -> List[Dict[str, Any]]:
        """
        Create objective relationship mapping data

        This method:
        1. Fetches all objectives
        2. Filters by status (active vs all)
        3. Separates into company objectives (no team_ids) and team objectives (with team_ids)
        4. Creates Cartesian product: company_obj × team_obj
        5. Resolves team names for team objectives

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 200)
            filters: Optional API filters
            get_all: Fetch all pages (default: False)
            status_filter: "active" or "all" (default: "active")
            team_mapping: Optional dict of team_id -> team_name for resolution
                         If None, fetches teams internally (one API call)

        Returns:
            List of mapping row dictionaries with structure:
            {
                'company_objective_name': company objective name,
                'team_objective_name': team objective name,
                'team_name': resolved team name,
                'company_objective_id': company objective ID,
                'team_objective_id': team objective ID
            }

        Side effects:
            Prints counts of company/team objectives and total mappings

        Example:
            If 2 company objectives and 3 team objectives:
            Returns 2 × 3 = 6 mapping rows
        """
        # Apply status filtering if needed
        if filters is None:
            filters = {}

        if status_filter == "active":
            filters["location_status"] = "active"
            print("Filtering for active objectives only")
        elif status_filter == "all":
            print("Getting all objectives regardless of status")

        print(f"Applying filters: {filters}")

        print("Fetching objectives for mapping...")
        objectives_response = self.get_objectives(page, page_size, filters, get_all)

        if 'results' not in objectives_response:
            print("No results found in objectives response")
            return []

        objectives = objectives_response['results']

        # If we're filtering for active objectives, also filter the results after fetching
        if status_filter == "active":
            original_count = len(objectives)
            objectives = [obj for obj in objectives if
                obj.get('location_status') == 'active' or
                (obj.get('location_status') != 'archived' and
                 obj.get('location_status') != 'inactive')]
            print(f"Filtered objectives from {original_count} to {len(objectives)} active objectives")

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

        # Separate company-level and team-level objectives
        company_objectives = []
        team_objectives = []

        for obj in objectives:
            team_ids = obj.get('team_ids', [])
            # Objectives with no team_ids (or empty list) are company-level
            if not team_ids or (isinstance(team_ids, list) and len(team_ids) == 0):
                company_objectives.append(obj)
            else:
                team_objectives.append(obj)

        print(f"Found {len(company_objectives)} company-level objectives")
        print(f"Found {len(team_objectives)} team-level objectives")

        # Create mapping rows - Cartesian product of company objectives x team objectives
        mapping_rows = []

        for company_obj in company_objectives:
            for team_obj in team_objectives:
                # Get team names for the team objective
                team_ids = team_obj.get('team_ids', [])
                team_names = []

                if team_ids:
                    # Ensure team_ids is a list
                    if not isinstance(team_ids, list):
                        team_ids = [team_ids]

                    for team_id in team_ids:
                        if team_id in team_mapping:
                            team_names.append(team_mapping[team_id])

                team_name = ', '.join(team_names) if team_names else 'Unknown Team'

                row = {
                    'company_objective_name': company_obj.get('name', ''),
                    'team_objective_name': team_obj.get('name', ''),
                    'team_name': team_name,
                    'company_objective_id': company_obj.get('id', ''),
                    'team_objective_id': team_obj.get('id', '')
                }
                mapping_rows.append(row)

        print(f"Generated {len(mapping_rows)} mapping rows ({len(company_objectives)} company × {len(team_objectives)} team objectives)")
        return mapping_rows
