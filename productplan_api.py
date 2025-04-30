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
		except FileNotFoundError:
			print(f"Error: Token file '{token_file}' not found.")
			print("Please create this file with your ProductPlan API token.")
			sys.exit(1)
			
		self.headers = {
			"accept": "application/json",
			"authorization": f"Bearer {self.token}"
		}
	
	def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""Make a GET request to the API"""
		url = f"{self.BASE_URL}/{endpoint}"
		
		try:
			response = requests.get(url, headers=self.headers, params=params)
			response.raise_for_status()  # Raise exception for 4XX/5XX responses
			return response.json()
		except requests.exceptions.RequestException as e:
			print(f"API request failed: {e}")
			sys.exit(1)
	
	def get_ideas(self, page: int = 1, page_size: int = 200, filters: Optional[Dict[str, Any]] = None, get_all: bool = False) -> Dict[str, Any]:
		"""
		Get ideas from the ProductPlan API
		
		If get_all is True, will fetch all pages and combine them into one response
		"""
		if not get_all:
			params = {
				"page": page,
				"page_size": page_size
			}
			
			# Add filters if provided
			if filters:
				params["q"] = json.dumps(filters)
				
			return self._make_request("discovery/ideas", params)
		else:
			# Get all pages
			all_ideas = []
			current_page = 1
			more_pages = True
			
			print("Fetching all ideas...")
			
			while more_pages:
				print(f"Fetching page {current_page}...")
				params = {
					"page": current_page,
					"page_size": page_size
				}
				
				# Add filters if provided
				if filters:
					params["q"] = json.dumps(filters)
				
				response = self._make_request("discovery/ideas", params)
				
				if 'ideas' in response and response['ideas']:
					all_ideas.extend(response['ideas'])
					current_page += 1
					print(f"Fetched {len(response['ideas'])} ideas. Total so far: {len(all_ideas)}")
				else:
					more_pages = False
			
			print(f"Finished fetching all ideas. Total: {len(all_ideas)}")
			# Return in same format as regular response
			result = response.copy()
			result['ideas'] = all_ideas
			return result
	
	# You can add more API methods here in the future


class DataExporter:
	"""Export API data to different formats"""
	
	@staticmethod
	def to_excel(data: List[Dict[str, Any]], filename: str) -> None:
		"""Export data to Excel file"""
		df = pd.DataFrame(data)
		df.to_excel(filename, index=False)
		print(f"Data exported to {filename}")


def parse_arguments():
	"""Parse command line arguments"""
	parser = argparse.ArgumentParser(description='ProductPlan API Client')
	
	parser.add_argument('--endpoint', default='ideas', 
						choices=['ideas'], 
						help='API endpoint to query (default: ideas)')
	
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
	
	# Initialize API client
	api = ProductPlanAPI(args.token_file)
	
	# Prepare filters if provided
	filters = None
	if args.filter:
		filters = {key: value for key, value in args.filter}
	
	# Call appropriate API endpoint
	if args.endpoint == 'ideas':
		response = api.get_ideas(args.page, args.page_size, filters, args.all_pages)
		if 'ideas' in response:
			DataExporter.to_excel(response['ideas'], args.output)
		else:
			print("Error: Unexpected API response format")
			sys.exit(1)
	else:
		print(f"Error: Endpoint '{args.endpoint}' not implemented")
		sys.exit(1)


if __name__ == "__main__":
	main()