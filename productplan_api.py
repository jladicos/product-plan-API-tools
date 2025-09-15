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
	
	def get_idea_details(self, idea_id: int) -> Dict[str, Any]:
		"""Get detailed information for a specific idea by ID"""
		endpoint = f"discovery/ideas/{idea_id}"
		print(f"Fetching detailed information for idea ID: {idea_id}")
		return self._make_request(endpoint)
			
	def get_teams(self, page: int = 1, page_size: int = 200, 
				 filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""Get teams from the ProductPlan API"""
		return self.get_data("teams", page, page_size, filters, get_all)
	
	def get_idea_forms(self, page: int = 1, page_size: int = 200, 
					  filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""Get idea forms from the ProductPlan API"""
		return self.get_data("discovery/idea_forms", page, page_size, filters, get_all)
	
	def get_idea_form_details(self, form_id: int) -> Dict[str, Any]:
		"""Get detailed information for a specific idea form by ID"""
		endpoint = f"discovery/idea_forms/{form_id}"
		print(f"Fetching detailed information for idea form ID: {form_id}")
		return self._make_request(endpoint)

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
	
	def get_enhanced_idea_forms(self, page: int = 1, page_size: int = 200, 
							   filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> List[Dict[str, Any]]:
		"""
		Get idea forms with enhanced details by fetching individual form information
		
		Returns:
			List of enhanced idea form dictionaries with detailed information
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
		return self.get_data("strategy/objectives", page, page_size, filters, get_all)
	
	def get_objective_details(self, objective_id: int) -> Dict[str, Any]:
		"""
		Get detailed information for a specific objective by ID
		
		Args:
			objective_id: The unique ID of the objective to fetch
			
		Returns:
			Detailed objective data including team assignments, status, timestamps, etc.
		"""
		endpoint = f"strategy/objectives/{objective_id}"
		print(f"Fetching detailed information for objective ID: {objective_id}")
		return self._make_request(endpoint)
	
	def get_key_results(self, objective_id: int, page: int = 1, page_size: int = 200, 
					   filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""
		Get key results for a specific objective from the ProductPlan API
		
		Args:
			objective_id: The ID of the objective to fetch key results for
			page: Page number to fetch (default: 1)
			page_size: Number of items per page (default: 200, max: 500)
			filters: Dictionary of filter key-value pairs to apply
			get_all: If True, fetches all pages of results
			
		Returns:
			API response containing key results data with 'results' key
			Each key result includes description (name), target, current, progress, team assignments
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
	
	def get_enhanced_okr_data(self, page: int = 1, page_size: int = 200, 
							 filters: Optional[Dict[str, Any]] = None, get_all: bool = False,
							 status_filter: str = "active") -> List[Dict[str, Any]]:
		"""
		Get objectives with their key results in a flattened format suitable for Excel/Markdown export
		
		This method fetches objectives from ProductPlan's strategy API and their associated key results,
		then flattens the data into a tabular format where each row represents either an objective
		without key results or a key result with its parent objective information.
		
		The method handles:
		- Active objective filtering by default (configurable)
		- Team name resolution from team IDs
		- Detailed objective and key result data fetching
		- Proper handling of objectives with no key results
		- Error handling for individual objective/key result fetching
		
		Column structure (Excel format):
		- status: Objective location status 
		- team_name: Resolved team name(s) from team IDs
		- objective_name: Objective title/name
		- objective_description: Objective description
		- key_result_name: Key result description (from 'description' field)
		- key_result_target: Target value for the key result
		- key_result_current: Current value/progress
		- key_result_progress: Progress percentage or metric
		- objective_id: Unique objective identifier (at end for reference)
		- key_result_id: Unique key result identifier (at end for reference)
		
		Args:
			page: Page number to start fetching from (default: 1)
			page_size: Number of objectives per page (default: 200, max: 500)
			filters: Additional API filters as key-value pairs
			get_all: If True, fetches all pages of objectives (default: False)
			status_filter: Objective status filter - "active" (default) or "all"
				- "active": Only returns active objectives (excludes archived/inactive)
				- "all": Returns all objectives regardless of status
		
		Returns:
			List of dictionaries where each dictionary represents one row:
			- If objective has key results: one row per key result (no separate objective row)
			- If objective has no key results: one row for the objective with empty key result fields
			
		Raises:
			SystemExit: If no objectives are found or API calls fail
			
		Note:
			- Team names are resolved once at the start to avoid API hammering
			- Key result names come from the 'description' field in the API response
			- Multiple team IDs are joined with commas in team_name field
			- Debug output shows team mapping and objective processing details
		"""
		# Apply status filtering if needed
		if filters is None:
			filters = {}
		
		if status_filter == "active":
			# Try different possible field names for objective status
			# The exact field name might be different - these are common possibilities
			filters["location_status"] = "active"  # Most likely based on ideas API
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
		
		# Get team mapping for team names
		team_mapping = self.get_team_id_to_name_mapping()
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
				
				# Get key results for this objective
				key_results_response = self.get_key_results(objective_id, get_all=True)
				
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

	def get_enhanced_ideas(self, page: int = 1, page_size: int = 200, 
						  filters: Optional[Dict[str, Any]] = None, get_all: bool = False,
						  location_status: str = "not_archived") -> List[Dict[str, Any]]:
		"""
		Get ideas with enhanced details by fetching individual idea information
		
		Args:
			page: Page number
			page_size: Number of items per page
			filters: Additional filters to apply
			get_all: Whether to fetch all pages
			location_status: Filter by location status ("all", "visible", "hidden", "archived", "not_archived")
		
		Returns:
			List of enhanced idea dictionaries with detailed information
		"""
		# Set up location_status filter
		if filters is None:
			filters = {}
		
		# Handle location_status filtering
		if location_status in ["not_archived", "archived", "visible", "hidden"]:
			# These will require checking the detailed data since we need to filter precisely
			print(f"Filtering for location_status: {location_status} (will be applied after fetching detailed data)")
		elif location_status != "all":
			# Apply the filter directly to the API call for any other values
			filters["location_status"] = location_status
			print(f"Filtering for location_status: {location_status}")
		else:
			print("Getting all ideas regardless of location_status")
		
		print("Fetching ideas list...")
		ideas_response = self.get_ideas(page, page_size, filters, get_all)
		
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
	def to_markdown_okr(okr_data: List[Dict[str, Any]], filename: str) -> None:
		"""
		Export OKR data to a structured Markdown file
		
		This method takes flattened OKR data (from get_enhanced_okr_data) and converts it
		into a well-structured Markdown document with proper headings and formatting.
		
		Markdown structure generated:
		- H1: "Objectives and Key Results" (document title)
		- H2: Objective name (without team in parentheses)
		- Objective description (if available)
		- H3: "Team" section with team name
		- H3: "Key Results" section
		- Bulleted list of key results with targets in parentheses
		- "No key results" message if objective has no key results
		
		Key result format: "- Key result description (target: value) - Current: X | Progress: Y"
		
		Args:
			okr_data: List of OKR row dictionaries from get_enhanced_okr_data()
			filename: Output markdown filename (e.g., "okrs.md")
			
		Returns:
			None (writes file to disk)
			
		Raises:
			Exception: If file writing fails
			
		Example output:
		```markdown
		# Objectives and Key Results
		
		## Increase User Engagement
		Improve user engagement across all product features.
		
		### Team
		Product Team
		
		### Key Results
		- Increase daily active users by 25% (target: 10000) - Current: 8000 | Progress: 80%
		- Reduce churn rate (target: 5%) - Current: 7% | Progress: 60%
		```
		"""
		if not okr_data:
			print("Warning: No OKR data to export")
			return
		
		print(f"Exporting OKR data to markdown format: {filename}")
		
		# Group data by objectives
		objectives = {}
		for row in okr_data:
			obj_id = row.get('objective_id', '')
			obj_name = row.get('objective_name', 'Unknown Objective')
			obj_description = row.get('objective_description', '')
			
			if obj_id not in objectives:
				objectives[obj_id] = {
					'name': obj_name,
					'description': obj_description,
					'team_name': row.get('team_name', ''),
					'status': row.get('status', ''),
					'key_results': []
				}
			
			# Add key result if it exists
			kr_name = row.get('key_result_name', '').strip()
			if kr_name:
				kr_data = {
					'name': kr_name,
					'target': row.get('key_result_target', ''),
					'current': row.get('key_result_current', ''),
					'progress': row.get('key_result_progress', '')
				}
				objectives[obj_id]['key_results'].append(kr_data)
		
		# Generate markdown content
		markdown_lines = []
		markdown_lines.append("# Objectives and Key Results")
		markdown_lines.append("")
		
		for obj_id, obj_data in objectives.items():
			# Objective heading (without team name)
			markdown_lines.append(f"## {obj_data['name']}")
			
			# Objective description
			if obj_data['description']:
				markdown_lines.append(obj_data['description'])
				markdown_lines.append("")
			
			# Team section
			if obj_data['team_name']:
				markdown_lines.append("### Team")
				markdown_lines.append(obj_data['team_name'])
				markdown_lines.append("")
			
			# Key results section
			markdown_lines.append("### Key Results")
			
			if obj_data['key_results']:
				for kr in obj_data['key_results']:
					kr_line = f"- {kr['name']}"
					
					# Add target in parentheses if available
					if kr['target']:
						kr_line += f" (target: {kr['target']})"
					
					# Add other details after the target
					details = []
					if kr['current']:
						details.append(f"Current: {kr['current']}")
					if kr['progress']:
						details.append(f"Progress: {kr['progress']}")
					
					if details:
						kr_line += f" - {' | '.join(details)}"
					
					markdown_lines.append(kr_line)
				markdown_lines.append("")
			else:
				markdown_lines.append("No key results")
				markdown_lines.append("")
		
		# Write to file
		try:
			with open(filename, 'w', encoding='utf-8') as f:
				f.write('\n'.join(markdown_lines))
			
			abs_path = os.path.abspath(filename)
			print(f"OKR data successfully exported to {abs_path}")
			print(f"Generated markdown for {len(objectives)} objectives")
		except Exception as e:
			print(f"Error exporting to markdown: {e}")
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
	def add_custom_dropdown_columns(idea: Dict[str, Any], field_labels: set) -> Dict[str, Any]:
		"""
		Add custom dropdown field columns to a single idea
		
		Args:
			idea: Original idea dictionary
			field_labels: Set of all possible custom dropdown field labels
			
		Returns:
			Modified idea dictionary with custom dropdown field columns
		"""
		# Use the input idea (which may already have other custom fields added)
		processed_idea = idea
		
		# Initialize all custom dropdown field columns with empty strings
		for label in field_labels:
			processed_idea[f"Custom_Dropdown: {label}"] = ""
			
		# Process custom dropdown fields from detailed API response
		custom_dropdown_fields = idea.get('custom_dropdown_fields', [])
		if isinstance(custom_dropdown_fields, list):
			for field in custom_dropdown_fields:
				if isinstance(field, dict) and 'label' in field and 'value' in field:
					processed_idea[f"Custom_Dropdown: {field['label']}"] = field['value']
				
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
		# First pass: collect all unique custom field labels for both text and dropdown fields
		all_text_field_labels = set()
		all_dropdown_field_labels = set()
		print("Collecting unique custom field labels...")
		
		for idea in ideas_data:
			# Process custom text fields
			custom_text_fields = DataExporter.parse_custom_text_fields(idea.get('custom_text_fields'))
			for field in custom_text_fields:
				if isinstance(field, dict) and 'label' in field:
					all_text_field_labels.add(field['label'])
			
			# Process custom dropdown fields (from detailed API response)
			custom_dropdown_fields = idea.get('custom_dropdown_fields', [])
			if isinstance(custom_dropdown_fields, list):
				for field in custom_dropdown_fields:
					if isinstance(field, dict) and 'label' in field:
						all_dropdown_field_labels.add(field['label'])
		
		print(f"Found {len(all_text_field_labels)} unique custom text field labels: {all_text_field_labels}")
		print(f"Found {len(all_dropdown_field_labels)} unique custom dropdown field labels: {all_dropdown_field_labels}")
		
		# Second pass: add custom field columns and team columns
		processed_ideas = []
		print("Processing ideas data (adding custom fields and team columns)...")
		
		for idea in ideas_data:
			# Start with the original idea data
			processed_idea = idea.copy()
			
			# Add custom text field columns
			processed_idea = DataExporter.add_custom_field_columns(processed_idea, all_text_field_labels)
			
			# Add custom dropdown field columns
			processed_idea = DataExporter.add_custom_dropdown_columns(processed_idea, all_dropdown_field_labels)
			
			# Add team columns
			processed_idea = DataExporter.add_team_columns(processed_idea, team_mapping)
			
			# Add to the result list
			processed_ideas.append(processed_idea)
		
		return processed_ideas
	
	@staticmethod
	def process_idea_forms(forms_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""
		Process idea forms data to flatten custom fields for better Excel export
		
		Args:
			forms_data: List of enhanced idea form dictionaries
			
		Returns:
			List of processed idea form dictionaries with flattened custom fields
		"""
		processed_forms = []
		print("Processing idea forms data (flattening custom fields)...")
		
		for form in forms_data:
			# Start with the original form data
			processed_form = form.copy()
			
			# Process custom text fields
			if 'custom_text_fields' in form and form['custom_text_fields']:
				custom_text_fields = form['custom_text_fields']
				if isinstance(custom_text_fields, list):
					for i, field in enumerate(custom_text_fields):
						if isinstance(field, dict) and 'label' in field:
							processed_form[f"Custom_Text_Field_{i+1}_Label"] = field['label']
							# Include other properties if they exist
							for key, value in field.items():
								if key != 'label':
									processed_form[f"Custom_Text_Field_{i+1}_{key}"] = value
				
				# Remove the original nested field to avoid confusion
				processed_form.pop('custom_text_fields', None)
			
			# Process custom dropdown fields
			if 'custom_dropdown_fields' in form and form['custom_dropdown_fields']:
				custom_dropdown_fields = form['custom_dropdown_fields']
				if isinstance(custom_dropdown_fields, list):
					for i, field in enumerate(custom_dropdown_fields):
						if isinstance(field, dict) and 'label' in field:
							processed_form[f"Custom_Dropdown_Field_{i+1}_Label"] = field['label']
							# Handle allowed_values as a comma-separated string
							if 'allowed_values' in field and isinstance(field['allowed_values'], list):
								processed_form[f"Custom_Dropdown_Field_{i+1}_Allowed_Values"] = ', '.join(field['allowed_values'])
							# Include other properties if they exist
							for key, value in field.items():
								if key not in ['label', 'allowed_values']:
									processed_form[f"Custom_Dropdown_Field_{i+1}_{key}"] = value
				
				# Remove the original nested field to avoid confusion
				processed_form.pop('custom_dropdown_fields', None)
			
			processed_forms.append(processed_form)
		
		print(f"Processed {len(processed_forms)} idea forms with flattened custom fields")
		return processed_forms


def parse_arguments():
	"""Parse command line arguments"""
	parser = argparse.ArgumentParser(description='ProductPlan API Client')
	
	parser.add_argument('--endpoint', default='ideas', 
						choices=['ideas', 'teams', 'idea-forms', 'okrs'], 
						help='API endpoint to query (default: ideas, available: teams, idea-forms, okrs)')
	
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
	
	parser.add_argument('--location-status', default='not_archived',
					   choices=['all', 'visible', 'hidden', 'archived', 'not_archived'],
					   help='Filter ideas by location status (default: not_archived, available: all, visible, hidden, archived, not_archived)')
	
	parser.add_argument('--objective-status', default='active',
					   choices=['active', 'all'],
					   help='Filter objectives by status (default: active, available: active, all)')
	
	parser.add_argument('--output-format', default='excel',
					   choices=['excel', 'markdown'],
					   help='Output format for OKRs (default: excel, available: excel, markdown)')
	
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
		print(f"Fetching ideas with detailed information from ProductPlan API")
		print(f"Location status filter: {args.location_status}")
		
		# Get enhanced ideas data (this includes detailed information for each idea)
		enhanced_ideas = api.get_enhanced_ideas(args.page, args.page_size, filters, args.all_pages, args.location_status)
		
		if enhanced_ideas:
			# Get team mapping first (requires API call)
			team_mapping = api.get_team_id_to_name_mapping()
			
			# Process the enhanced ideas data (includes custom text fields, dropdown fields, and team columns)
			processed_data = DataExporter.process_ideas(enhanced_ideas, team_mapping)
			
			DataExporter.to_excel(processed_data, args.output)
		else:
			print("Error: No ideas data received")
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
			
	elif args.endpoint == 'idea-forms':
		print(f"Fetching idea forms with detailed information from ProductPlan API")
		
		# Get enhanced idea forms data (this includes detailed information for each form)
		enhanced_forms = api.get_enhanced_idea_forms(args.page, args.page_size, filters, args.all_pages)
		
		if enhanced_forms:
			# Process the enhanced forms data (flatten custom fields for Excel export)
			processed_forms = DataExporter.process_idea_forms(enhanced_forms)
			DataExporter.to_excel(processed_forms, args.output)
		else:
			print("Error: No idea forms data received")
			sys.exit(1)
			
	elif args.endpoint == 'okrs':
		print(f"Fetching objectives and key results from ProductPlan API")
		print(f"Objective status filter: {args.objective_status}")
		print(f"Output format: {args.output_format}")
		
		# Get OKR data in flattened format
		okr_data = api.get_enhanced_okr_data(args.page, args.page_size, filters, args.all_pages, args.objective_status)
		
		if okr_data:
			if args.output_format == 'markdown':
				# Default to okrs.md if no output specified and format is markdown
				output_file = args.output
				if args.output == 'output.xlsx':  # Default Excel filename
					output_file = 'okrs.md'
				elif output_file.endswith('.xlsx'):  # User specified Excel file but wants markdown
					output_file = output_file.replace('.xlsx', '.md')
				DataExporter.to_markdown_okr(okr_data, output_file)
			else:  # excel format
				DataExporter.to_excel(okr_data, args.output)
		else:
			print("Error: No OKR data received")
			sys.exit(1)
	else:
		print(f"Error: Endpoint '{args.endpoint}' not implemented")
		sys.exit(1)


if __name__ == "__main__":
	main()