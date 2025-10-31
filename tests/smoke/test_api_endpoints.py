"""
Smoke tests for ProductPlan API endpoints

These tests hit the real ProductPlan API to verify endpoints are working.
Requires valid token.txt file.
"""
import pytest
import os
from pathlib import Path

# Import resources from new package
from productplan_api_tools.api.teams import TeamsResource
from productplan_api_tools.api.ideas import IdeasResource
from productplan_api_tools.api.okrs import OKRsResource
from productplan_api_tools.api.idea_forms import IdeaFormsResource
from productplan_api_tools.api.objective_maps import ObjectiveMappingResource


# Fixture to check for token file
@pytest.fixture(scope="module")
def token_file():
    """Check if token file exists, skip tests if not"""
    token_path = Path("token.txt")
    if not token_path.exists():
        pytest.skip("token.txt not found - skipping smoke tests")
    return str(token_path)


class TestTeamsEndpoint:
    """Smoke tests for teams endpoint"""

    def test_teams_endpoint_works(self, token_file):
        """Verify teams endpoint returns valid data"""
        resource = TeamsResource(token_file)

        # Fetch teams (just first page, small page size)
        response = resource.fetch_list(page=1, page_size=5, get_all=False)

        # Verify response structure
        assert 'results' in response
        assert 'paging' in response
        assert isinstance(response['results'], list)

        # If there are teams, verify structure
        if response['results']:
            team = response['results'][0]
            assert 'id' in team
            assert 'name' in team

    def test_teams_id_to_name_mapping(self, token_file):
        """Verify team mapping functionality works"""
        resource = TeamsResource(token_file)

        # Build mapping
        mapping = resource.build_id_to_name_mapping()

        # Verify it's a dictionary
        assert isinstance(mapping, dict)

        # If there are teams, verify structure
        if mapping:
            team_id = list(mapping.keys())[0]
            team_name = mapping[team_id]
            assert isinstance(team_id, int)
            assert isinstance(team_name, str)


class TestIdeasEndpoint:
    """Smoke tests for ideas endpoint"""

    def test_ideas_endpoint_works(self, token_file):
        """Verify ideas endpoint returns valid data"""
        resource = IdeasResource(token_file)

        # Fetch ideas (small sample)
        response = resource.fetch_list(page=1, page_size=3, get_all=False)

        # Verify response structure
        assert 'results' in response
        assert 'paging' in response
        assert isinstance(response['results'], list)

    def test_ideas_detailed_fetch(self, token_file):
        """Verify detailed idea fetch works"""
        resource = IdeasResource(token_file)

        # Fetch one idea
        response = resource.fetch_list(page=1, page_size=1, get_all=False)

        if response['results']:
            idea = response['results'][0]
            idea_id = idea['id']

            # Fetch detailed info
            detailed = resource.fetch_details(idea_id)

            # Verify additional fields from detailed endpoint
            assert 'id' in detailed
            # Note: location_status may or may not be in list response
            # but should be in detailed response


class TestOKRsEndpoint:
    """Smoke tests for OKRs endpoint"""

    def test_objectives_endpoint_works(self, token_file):
        """Verify objectives endpoint returns valid data"""
        resource = OKRsResource(token_file)

        # Fetch objectives (small sample)
        response = resource.fetch_list(page=1, page_size=2, get_all=False)

        # Verify response structure
        assert 'results' in response
        assert 'paging' in response
        assert isinstance(response['results'], list)

    def test_key_results_endpoint_works(self, token_file):
        """Verify key results endpoint works"""
        resource = OKRsResource(token_file)

        # Fetch objectives
        response = resource.fetch_list(page=1, page_size=2, get_all=False)

        if response['results']:
            objective = response['results'][0]
            objective_id = objective['id']

            # Fetch key results for this objective
            kr_response = resource.fetch_key_results(objective_id, get_all=False)

            # Verify structure (may or may not have key results)
            assert 'results' in kr_response
            assert isinstance(kr_response['results'], list)


class TestIdeaFormsEndpoint:
    """Smoke tests for idea forms endpoint"""

    def test_idea_forms_endpoint_works(self, token_file):
        """Verify idea forms endpoint returns valid data"""
        resource = IdeaFormsResource(token_file)

        # Fetch idea forms (small sample)
        response = resource.fetch_list(page=1, page_size=2, get_all=False)

        # Verify response structure
        assert 'results' in response
        assert 'paging' in response
        assert isinstance(response['results'], list)


class TestObjectiveMappingEndpoint:
    """Smoke tests for objective mapping endpoint"""

    def test_objective_mapping_uses_objectives_endpoint(self, token_file):
        """Verify objective mapping can fetch objectives"""
        resource = ObjectiveMappingResource(token_file)

        # Fetch objectives (uses strategy/objectives endpoint)
        response = resource.fetch_list(page=1, page_size=2, get_all=False)

        # Verify response structure
        assert 'results' in response
        assert 'paging' in response
        assert isinstance(response['results'], list)


class TestAuthentication:
    """Smoke tests for authentication"""

    def test_authentication_works(self, token_file):
        """Verify token authentication is working"""
        resource = TeamsResource(token_file)

        # This should succeed without raising authentication errors
        response = resource.fetch_list(page=1, page_size=1, get_all=False)

        # If we get here without exception, auth worked
        assert 'results' in response

    def test_invalid_token_fails(self):
        """Verify invalid token is rejected"""
        # Create temp file with invalid token
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('invalid_token_12345')
            temp_token = f.name

        try:
            resource = TeamsResource(temp_token)

            # This should fail with authentication error
            with pytest.raises(SystemExit):  # Our code calls sys.exit(1) on auth failure
                resource.fetch_list(page=1, page_size=1, get_all=False)
        finally:
            # Clean up temp file
            os.unlink(temp_token)
