"""
Ideas Resource

Handles ideas endpoint with enhanced detail fetching and location filtering.
"""

from typing import Dict, List, Any, Optional
from productplan_api_tools.api.client import BaseResource


class IdeasResource(BaseResource):
    """
    Resource for ProductPlan ideas API

    Provides:
    - Standard list/details fetching (inherited)
    - Enhanced fetching with detailed information per idea
    - Location status filtering (archived, visible, hidden, etc.)
    """

    @property
    def endpoint_path(self) -> str:
        """Returns: "discovery/ideas" """
        return "discovery/ideas"

    def get_ideas(self, page: int = 1, page_size: int = 200,
                  filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
        """
        Get ideas from the ProductPlan API

        This is a convenience method that calls fetch_list with the ideas endpoint.

        Args:
            page: Page number
            page_size: Items per page
            filters: Optional filters
            get_all: Fetch all pages

        Returns:
            API response with ideas data
        """
        return self.fetch_list(
            page=page,
            page_size=page_size,
            filters=filters,
            get_all=get_all
        )

    def get_idea_details(self, idea_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific idea by ID

        Args:
            idea_id: The unique ID of the idea

        Returns:
            Detailed idea data
        """
        return self.fetch_details(idea_id)

    def fetch_enhanced(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None,
                      get_all: bool = False,
                      location_status: str = "not_archived") -> List[Dict[str, Any]]:
        """
        Fetch ideas with enhanced details for each idea

        This method:
        1. Fetches list of ideas (basic info)
        2. For each idea, fetches detailed information (includes custom fields, timestamps, etc.)
        3. Filters by location_status after fetching details
        4. Returns enhanced idea dictionaries

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 200)
            filters: Optional API filters
            get_all: Fetch all pages (default: False)
            location_status: Filter by status (default: "not_archived")
                Options: "all", "visible", "hidden", "archived", "not_archived"

        Returns:
            List of enhanced idea dictionaries with detailed information

        Side effects:
            Prints progress for each idea fetched

        Note:
            Location filtering happens AFTER fetching details because the detailed
            endpoint provides more accurate location_status than the list endpoint
        """
        # Set up location_status filter message
        if location_status in ["not_archived", "archived", "visible", "hidden"]:
            print(f"Filtering for location_status: {location_status} (will be applied after fetching detailed data)")
        elif location_status != "all":
            filters = filters or {}
            filters["location_status"] = location_status
            print(f"Filtering for location_status: {location_status}")
        else:
            print("Getting all ideas regardless of location_status")

        print("Fetching ideas list...")
        ideas_response = self.get_ideas(
            page=page,
            page_size=page_size,
            filters=filters,
            get_all=get_all
        )

        if 'results' not in ideas_response:
            print("No results found in ideas response")
            return []

        ideas = ideas_response['results']
        enhanced_ideas = []

        print(f"Fetching detailed information for {len(ideas)} ideas...")

        for i, idea in enumerate(ideas, 1):
            if 'id' not in idea:
                print(f"Warning: Idea {i} has no ID, skipping detailed fetch")
                enhanced_ideas.append(idea)
                continue

            try:
                idea_id = idea['id']
                print(f"Processing idea {i}/{len(ideas)}: ID {idea_id}")

                # Get detailed information for this idea
                detailed_idea = self.get_idea_details(idea_id)

                # Merge the detailed information with the original idea data
                enhanced_idea = {**idea, **detailed_idea}

                # Apply location_status filtering based on the detailed data
                idea_location_status = enhanced_idea.get('location_status', '')

                # Filter based on location_status parameter
                if location_status == "not_archived":
                    if idea_location_status == 'archived':
                        print(f"Skipping archived idea ID {idea_id} (status: {idea_location_status})")
                        continue
                elif location_status == "archived":
                    if idea_location_status != 'archived':
                        print(f"Skipping non-archived idea ID {idea_id} (status: {idea_location_status})")
                        continue
                elif location_status == "visible":
                    if idea_location_status != 'visible':
                        print(f"Skipping non-visible idea ID {idea_id} (status: {idea_location_status})")
                        continue
                elif location_status == "hidden":
                    if idea_location_status != 'hidden':
                        print(f"Skipping non-hidden idea ID {idea_id} (status: {idea_location_status})")
                        continue
                # For location_status == "all", we don't filter anything

                enhanced_ideas.append(enhanced_idea)

            except Exception as e:
                print(f"Warning: Failed to fetch details for idea ID {idea.get('id', 'unknown')}: {e}")
                # If we can't get details, include the original idea data only if we're not filtering
                # or if we can determine the status from the basic data
                if location_status == "all":
                    enhanced_ideas.append(idea)
                elif location_status == "not_archived" and idea.get('location_status') != 'archived':
                    enhanced_ideas.append(idea)
                elif location_status in ["archived", "visible", "hidden"] and idea.get('location_status') == location_status:
                    enhanced_ideas.append(idea)
                # Otherwise skip this idea since we can't verify its status

        print(f"Successfully enhanced {len(enhanced_ideas)} ideas with detailed information")
        return enhanced_ideas
