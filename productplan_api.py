#!/usr/bin/env python3
# productplan_api.py

import os
import sys
import json
import argparse
import requests
import pandas as pd
from typing import Dict, Any, List, Optional


class ProductPlanAPI:
	"""Client for the ProductPlan API"""
	
	BASE_URL = "https://app.productplan.com/api/v2"
	
	def __init__(self, token_file: str = "token.txt"):
		"""Initialize the API client with a token from file"""
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
	
	def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""Make a GET request to the API"""
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
	
	def _fetch_all_pages(self, endpoint: str, page_size: int = 200, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""Generic method to fetch all pages of results from any endpoint"""
		all_results = []
		current_page = 1
		more_pages = True
		last_response = None
		resource_name = endpoint.split('/')[-1]  # Extract resource name for logging (e.g., "ideas", "teams")
		
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
	
	def get_data(self, endpoint: str, page: int = 1, page_size: int = 200, 
				 filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""
		Generic method to get data from any API endpoint
		
		Args:
			endpoint: API endpoint path relative to base URL (e.g., "discovery/ideas", "teams")
			page: Page number to fetch
			page_size: Number of items per page
			filters: Dictionary of filter key-value pairs
			get_all: If True, fetch all pages of results
			
		Returns:
			API response data
		"""
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
	
	def get_ideas(self, page: int = 1, page_size: int = 200, 
				 filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""Get ideas from the ProductPlan API"""
		return self.get_data("discovery/ideas", page, page_size, filters, get_all)
			
	def get_teams(self, page: int = 1, page_size: int = 200, 
				 filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""Get teams from the ProductPlan API"""
		return self.get_data("teams", page, page_size, filters, get_all)

	def get_team_id_to_name_mapping(self) -> Dict[int, str]:
		"""
		Get a mapping of team IDs to team names
		
		Returns:
			Dictionary mapping team IDs to team names
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


class DataExporter:
	"""Export API data to different formats"""
	
	@staticmethod
	def to_excel(data: List[Dict[str, Any]], filename: str) -> None:
		"""Export data to Excel file"""
		if not data:
			print("Warning: No data to export")
			return
			
		print(f"Exporting {len(data)} records to {filename}")
		try:
			df = pd.DataFrame(data)
			df.to_excel(filename, index=False)
			# Get full path to the output file
			abs_path = os.path.abspath(filename)
			print(f"Data successfully exported to {abs_path}")
		except Exception as e:
			print(f"Error exporting to Excel: {e}")
			raise
	
	@staticmethod
	def parse_custom_text_fields(custom_text_fields_data) -> List[Dict[str, Any]]:
		"""
		Parse custom text fields from various formats
		
		Args:
			custom_text_fields_data: Raw custom text fields data (string or list)
			
		Returns:
			List of parsed custom field dictionaries
		"""
		custom_fields = []
		
		if not custom_text_fields_data:
			return custom_fields
			
		# Handle different possible formats of custom_text_fields
		if isinstance(custom_text_fields_data, str):
			try:
				# Parse JSON string to list of dictionaries
				custom_fields = json.loads(custom_text_fields_data)
			except json.JSONDecodeError:
				# Log error only if there's actually content to parse
				if custom_text_fields_data.strip():
					print(f"Warning: Could not parse custom_text_fields: {custom_text_fields_data}")
		elif isinstance(custom_text_fields_data, list):
			custom_fields = custom_text_fields_data
			
		return custom_fields
	
	@staticmethod
	def parse_team_ids(team_ids_data) -> List[int]:
		"""
		Parse team IDs from various formats
		
		Args:
			team_ids_data: Raw team IDs data (string or list)
			
		Returns:
			List of parsed team IDs
		"""
		team_ids = []
		
		if not team_ids_data:
			return team_ids
			
		# Handle different possible formats of team_ids
		if isinstance(team_ids_data, list):
			team_ids = team_ids_data
		elif isinstance(team_ids_data, str):
			# Handle comma-separated string of team IDs
			try:
				team_ids = [int(tid.strip()) for tid in team_ids_data.split(',') if tid.strip()]
			except ValueError:
				print(f"Warning: Could not parse team_ids: {team_ids_data}")
				
		return team_ids
	
	@staticmethod
	def add_custom_field_columns(idea: Dict[str, Any], field_labels: set) -> Dict[str, Any]:
		"""
		Add custom field columns to a single idea
		
		Args:
			idea: Original idea dictionary
			field_labels: Set of all possible custom field labels
			
		Returns:
			Modified idea dictionary with custom field columns
		"""
		# Clone the idea dictionary
		processed_idea = idea.copy()
		
		# Initialize all custom field columns with empty strings
		for label in field_labels:
			processed_idea[f"Custom: {label}"] = ""
			
		# Parse and process custom text fields
		custom_fields = DataExporter.parse_custom_text_fields(idea.get('custom_text_fields'))
			
		# Add value to corresponding column
		for field in custom_fields:
			if isinstance(field, dict) and 'label' in field and 'value' in field:
				processed_idea[f"Custom: {field['label']}"] = field['value']
				
		return processed_idea
	
	@staticmethod
	def add_team_columns(idea: Dict[str, Any], team_mapping: Dict[int, str]) -> Dict[str, Any]:
		"""
		Add team columns to a single idea
		
		Args:
			idea: Original idea dictionary
			team_mapping: Dictionary mapping team IDs to team names
			
		Returns:
			Modified idea dictionary with team columns
		"""
		# Use the input idea (which may already have custom fields added)
		processed_idea = idea
		
		# Parse team IDs
		team_ids = DataExporter.parse_team_ids(idea.get('team_ids'))
		
		# Add columns for each team
		for team_id, team_name in team_mapping.items():
			# Set value to 1 if team_id is in team_ids, otherwise 0
			processed_idea[team_name] = 1 if team_id in team_ids else 0
			
		return processed_idea
		
	@staticmethod
	def process_ideas(ideas_data: List[Dict[str, Any]], team_mapping: Dict[int, str]) -> List[Dict[str, Any]]:
		"""
		Process ideas data to add both custom text field columns and team columns
		
		Args:
			ideas_data: List of idea dictionaries
			team_mapping: Dictionary mapping team IDs to team names
			
		Returns:
			List of processed idea dictionaries with added columns
		"""
		# First pass: collect all unique custom field labels
		all_field_labels = set()
		print("Collecting unique custom text field labels...")
		
		for idea in ideas_data:
			custom_fields = DataExporter.parse_custom_text_fields(idea.get('custom_text_fields'))
			for field in custom_fields:
				if isinstance(field, dict) and 'label' in field:
					all_field_labels.add(field['label'])
		
		print(f"Found {len(all_field_labels)} unique custom text field labels: {all_field_labels}")
		
		# Second pass: add both custom field and team columns
		processed_ideas = []
		print("Processing ideas data (adding custom fields and team columns)...")
		
		for idea in ideas_data:
			# First add custom field columns
			processed_idea = DataExporter.add_custom_field_columns(idea, all_field_labels)
			
			# Then add team columns (modifies the same dictionary)
			processed_idea = DataExporter.add_team_columns(processed_idea, team_mapping)
			
			# Add to the result list
			processed_ideas.append(processed_idea)
		
		return processed_ideas


def parse_arguments():
	"""Parse command line arguments"""
	parser = argparse.ArgumentParser(description='ProductPlan API Client')
	
	parser.add_argument('--endpoint', default='ideas', 
						choices=['ideas', 'teams'], 
						help='API endpoint to query (default: ideas, available: teams)')
	
	parser.add_argument('--token-file', default='token.txt',
					   help='File containing the API token (default: token.txt)')
	
	parser.add_argument('--page', type=int, default=1,
					   help='Page number (default: 1)')
	
	parser.add_argument('--page-size', type=int, default=200,
					   help='Number of items per page (default: 200)')
	
	parser.add_argument('--filter', action='append', nargs=2, metavar=('KEY', 'VALUE'),
					   help='Filter results (can be used multiple times)')
	
	parser.add_argument('--output', default='output.xlsx',
					   help='Output filename (default: output.xlsx)')
	
	parser.add_argument('--all-pages', action='store_true',
					   help='Fetch all pages of results')
	
	return parser.parse_args()


def main():
	"""Main function"""
	args = parse_arguments()
	
	print(f"Starting ProductPlan API Client")
	print(f"Output file: {args.output}")
	
	# Check if token file exists
	if not os.path.isfile(args.token_file):
		print(f"Error: Token file '{args.token_file}' not found")
		print("Please create this file with your ProductPlan API token")
		sys.exit(1)
	
	# Initialize API client
	api = ProductPlanAPI(args.token_file)
	
	# Prepare filters if provided
	filters = None
	if args.filter:
		filters = {key: value for key, value in args.filter}
		print(f"Applying filters: {filters}")
	
	# Check current directory is writable
	try:
		test_file = os.path.join(os.getcwd(), ".write_test")
		with open(test_file, "w") as f:
			f.write("test")
		os.remove(test_file)
	except IOError as e:
		print(f"Warning: Current directory may not be writable: {e}")
		print(f"Current working directory: {os.getcwd()}")
		print(f"Directory contents: {os.listdir('.')}")
	
	# Call appropriate API endpoint
	if args.endpoint == 'ideas':
		print(f"Fetching ideas from ProductPlan API")
		response = api.get_ideas(args.page, args.page_size, filters, args.all_pages)
		
		# Process response and export data
		if 'results' in response:
			# Get team mapping first (requires API call)
			team_mapping = api.get_team_id_to_name_mapping()
			
			# Process both custom text fields and team columns in a single pass
			processed_data = DataExporter.process_ideas(response['results'], team_mapping)
			
			DataExporter.to_excel(processed_data, args.output)
		else:
			print("Error: Unexpected API response format")
			print(f"Response keys: {response.keys()}")
			sys.exit(1)
			
	elif args.endpoint == 'teams':
		print(f"Fetching teams from ProductPlan API")
		response = api.get_teams(args.page, args.page_size, filters, args.all_pages)
		
		# Process response and export data
		if 'results' in response:
			DataExporter.to_excel(response['results'], args.output)
		else:
			print("Error: Unexpected API response format")
			print(f"Response keys: {response.keys()}")
			sys.exit(1)
	else:
		print(f"Error: Endpoint '{args.endpoint}' not implemented")
		sys.exit(1)


if __name__ == "__main__":
	main()