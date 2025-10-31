"""
API Resources

Contains all API resource classes for interacting with ProductPlan endpoints.
"""

from productplan_api_tools.api.client import BaseResource
from productplan_api_tools.api.teams import TeamsResource
from productplan_api_tools.api.ideas import IdeasResource
from productplan_api_tools.api.idea_forms import IdeaFormsResource
from productplan_api_tools.api.okrs import OKRsResource
from productplan_api_tools.api.objective_maps import ObjectiveMappingResource

__all__ = [
    'BaseResource',
    'TeamsResource',
    'IdeasResource',
    'IdeaFormsResource',
    'OKRsResource',
    'ObjectiveMappingResource'
]
