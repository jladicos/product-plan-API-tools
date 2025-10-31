"""
Teams Resource

Handles teams endpoint and provides team ID-to-name mapping.
"""

from typing import Dict
from productplan_api_tools.api.client import BaseResource


class TeamsResource(BaseResource):
    """
    Resource for ProductPlan teams API

    Provides:
    - Standard list/details fetching (inherited from BaseResource)
    - Team ID to name mapping utility
    """

    @property
    def endpoint_path(self) -> str:
        """Returns: "teams" """
        return "teams"

    def get_teams(self, page: int = 1, page_size: int = 200,
                  filters: Dict = None, get_all: bool = False) -> Dict:
        """
        Get teams from the ProductPlan API

        This is a convenience method that calls fetch_list with the teams endpoint.

        Args:
            page: Page number
            page_size: Items per page
            filters: Optional filters
            get_all: Fetch all pages

        Returns:
            API response with teams data
        """
        return self.fetch_list(page, page_size, filters, get_all)

    def build_id_to_name_mapping(self) -> Dict[int, str]:
        """
        Build a mapping of team IDs to team names

        Fetches all teams and creates a dictionary for quick lookups.
        Used by other resources to resolve team_ids to human-readable names.

        Returns:
            Dictionary mapping team ID (int) to team name (str)

        Side effects:
            Prints progress information and mapping size

        Example:
            {123: "Engineering", 456: "Product", 789: "Design"}
        """
        print("Fetching team data to build ID-to-name mapping...")
        teams_response = self.get_teams(get_all=True)

        team_map = {}
        if 'results' in teams_response:
            for team in teams_response['results']:
                if 'id' in team and 'name' in team:
                    team_map[team['id']] = team['name']

        print(f"Created mapping for {len(team_map)} teams")
        return team_map
