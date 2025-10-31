"""
Idea Forms Resource

Handles idea forms endpoint with enhanced detail fetching.
"""

from typing import Dict, List, Any, Optional
from productplan_api_tools.api.client import BaseResource


class IdeaFormsResource(BaseResource):
    """
    Resource for ProductPlan idea forms API

    Provides:
    - Standard list/details fetching (inherited)
    - Enhanced fetching with detailed information per form
    """

    @property
    def endpoint_path(self) -> str:
        """Returns: "discovery/idea_forms" """
        return "discovery/idea_forms"

    def get_idea_forms(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
        """
        Get idea forms from the ProductPlan API

        This is a convenience method that calls fetch_list with the idea forms endpoint.

        Args:
            page: Page number
            page_size: Items per page
            filters: Optional filters
            get_all: Fetch all pages

        Returns:
            API response with idea forms data
        """
        return self.fetch_list(page, page_size, filters, get_all)

    def get_idea_form_details(self, form_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific idea form by ID

        Args:
            form_id: The unique ID of the idea form

        Returns:
            Detailed form data
        """
        return self.fetch_details(form_id)

    def fetch_enhanced(self, page: int = 1, page_size: int = 200,
                      filters: Optional[Dict[str, Any]] = None,
                      get_all: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch idea forms with enhanced details for each form

        Similar to IdeasResource.fetch_enhanced but for forms.
        Fetches list, then gets details for each form.

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 200)
            filters: Optional API filters
            get_all: Fetch all pages (default: False)

        Returns:
            List of enhanced form dictionaries with custom field details

        Side effects:
            Prints progress for each form fetched
        """
        print("Fetching idea forms list...")
        forms_response = self.get_idea_forms(page, page_size, filters, get_all)

        if 'results' not in forms_response:
            print("No results found in idea forms response")
            return []

        forms = forms_response['results']
        enhanced_forms = []

        print(f"Fetching detailed information for {len(forms)} idea forms...")

        for i, form in enumerate(forms, 1):
            if 'id' not in form:
                print(f"Warning: Form {i} has no ID, skipping detailed fetch")
                enhanced_forms.append(form)
                continue

            try:
                form_id = form['id']
                print(f"Processing form {i}/{len(forms)}: ID {form_id}")

                # Get detailed information for this form
                detailed_form = self.get_idea_form_details(form_id)

                # Merge the detailed information with the original form data
                enhanced_form = {**form, **detailed_form}
                enhanced_forms.append(enhanced_form)

            except Exception as e:
                print(f"Warning: Failed to fetch details for form ID {form.get('id', 'unknown')}: {e}")
                # If we can't get details, include the original form data
                enhanced_forms.append(form)

        print(f"Successfully enhanced {len(enhanced_forms)} idea forms with detailed information")
        return enhanced_forms
