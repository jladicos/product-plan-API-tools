"""
Base API Resource Client

Provides common functionality for all ProductPlan API resources.
"""

import sys
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseResource(ABC):
    """
    Base class for ProductPlan API resources

    Provides common functionality:
    - Authentication with Bearer token
    - HTTP request handling with error handling
    - Automatic pagination for list endpoints
    - Basic fetch_list and fetch_details patterns

    Subclasses must implement:
    - endpoint_path: The API endpoint path (e.g., "discovery/ideas")
    """

    BASE_URL = "https://app.productplan.com/api/v2"

    def __init__(self, token_file: str = "token.txt"):
        """
        Initialize the API resource with authentication

        Args:
            token_file: Path to file containing ProductPlan API token

        Raises:
            FileNotFoundError: If token file doesn't exist
            SystemExit: If token file can't be read or is invalid
        """
        try:
            with open(token_file, 'r') as f:
                self.token = f.read().strip()
                print(f"Token loaded from {token_file}")
                # Print a partially masked token for debugging
                if len(self.token) > 8:
                    masked_token = self.token[:4] + "*" * (len(self.token) - 8) + self.token[-4:]
                    print(f"Token (partially masked): {masked_token}")
                else:
                    print("Warning: Token seems too short")
        except FileNotFoundError:
            print(f"Error: Token file '{token_file}' not found.")
            print("Please create this file with your ProductPlan API token.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading token file: {e}")
            sys.exit(1)

        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}"
        }

    @property
    @abstractmethod
    def endpoint_path(self) -> str:
        """
        The API endpoint path for this resource (relative to BASE_URL)

        Must be implemented by subclasses.

        Returns:
            Endpoint path string (e.g., "discovery/ideas", "teams")

        Note:
            Enforced at class definition time via ABC
        """
        pass

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API

        Args:
            endpoint: API endpoint path (relative to BASE_URL)
            params: Optional query parameters

        Returns:
            Parsed JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
            SystemExit: If request returns 4XX or 5XX status

        Side effects:
            Prints debug information (request URL, parameters, response status)
        """
        url = f"{self.BASE_URL}/{endpoint}"

        print(f"Making API request to: {url}")
        print(f"With parameters: {params}")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            print(f"Response status code: {response.status_code}")

            # Log any error message
            if response.status_code >= 400:
                print(f"Error response: {response.text}")

            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            result = response.json()
            print(f"Response keys: {result.keys()}")

            # Check for results key in the response
            if 'results' in result:
                print(f"Received {len(result['results'])} items")
            return result
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            sys.exit(1)

    def _fetch_all_pages(self, endpoint: str, page_size: int = 200,
                        filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch all pages of results from a paginated endpoint

        Continues fetching until no more pages available (paging.next is null).

        Args:
            endpoint: API endpoint path (relative to BASE_URL)
            page_size: Number of items per page (default: 200, max: 500)
            filters: Optional filter parameters (converted to q[key]=value format)

        Returns:
            Dictionary with 'results' key containing all items from all pages,
            and 'paging' key with pagination metadata from last response

        Side effects:
            Prints progress information for each page fetched
        """
        all_results = []
        current_page = 1
        more_pages = True
        last_response = None
        resource_name = endpoint.split('/')[-1]  # Extract resource name for logging

        print(f"Fetching all {resource_name}...")

        while more_pages:
            print(f"Fetching page {current_page}...")
            params = {
                "page": current_page,
                "page_size": page_size
            }

            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    params[f"q[{key}]"] = value

            response = self._make_request(endpoint, params)
            last_response = response

            # Check if we have results
            if 'results' in response and response['results']:
                items = response['results']
                all_results.extend(items)
                current_page += 1
                print(f"Fetched {len(items)} {resource_name}. Total so far: {len(all_results)}")

                # Check if there are more pages (using paging info)
                if 'paging' in response and 'next' in response['paging'] and response['paging']['next']:
                    more_pages = True
                else:
                    more_pages = False
            else:
                more_pages = False

        print(f"Finished fetching all {resource_name}. Total: {len(all_results)}")

        # Return in same format as regular response
        result = {'results': all_results}
        if last_response and 'paging' in last_response:
            result['paging'] = last_response['paging']
        return result

    def fetch_list(self, page: int = 1, page_size: int = 200,
                   filters: Optional[Dict[str, Any]] = None,
                   get_all: bool = False) -> Dict[str, Any]:
        """
        Fetch a list of items from this resource's endpoint

        Args:
            page: Page number to fetch (default: 1)
            page_size: Number of items per page (default: 200, max: 500)
            filters: Optional filter parameters
            get_all: If True, fetch all pages; if False, fetch single page

        Returns:
            API response with 'results' key containing items
        """
        if get_all:
            return self._fetch_all_pages(self.endpoint_path, page_size, filters)
        else:
            params = {
                "page": page,
                "page_size": page_size
            }

            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    params[f"q[{key}]"] = value

            return self._make_request(self.endpoint_path, params)

    def fetch_details(self, item_id: int) -> Dict[str, Any]:
        """
        Fetch detailed information for a single item

        Args:
            item_id: The unique ID of the item to fetch

        Returns:
            Detailed item data as dictionary

        Side effects:
            Prints debug information about the fetch
        """
        endpoint = f"{self.endpoint_path}/{item_id}"
        print(f"Fetching detailed information for item ID: {item_id}")
        return self._make_request(endpoint)
