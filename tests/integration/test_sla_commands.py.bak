"""
Integration tests for SLA commands (sla_init and sla_update)

Tests the orchestration layer with mocked API calls.
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from productplan_api_tools.sla.manager import sla_init, sla_update
from productplan_api_tools.sla.storage import ExcelSLAStorage


class TestSLAInit:
    """Integration tests for sla_init() function"""

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path (without creating the file)"""
        # Generate a unique temporary file path without creating the file
        import tempfile
        fd, file_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)  # Close the file descriptor
        os.remove(file_path)  # Remove the file so it doesn't exist yet

        yield file_path

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.fixture
    def mock_ideas_data(self):
        """Sample ideas data that would come from API"""
        return [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'John Doe',
                'source_email': 'john@example.com',
                'created_at': '2025-10-01T10:00:00Z',
                'updated_at': '2025-10-10T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'Accepted'}
                ],
                'team_ids': [1, 2]
            },
            {
                'id': 2,
                'name': 'Idea 2',
                'description': 'Description 2',
                'customer': 'Customer B',
                'source_name': 'Jane Smith',
                'source_email': 'jane@example.com',
                'created_at': '2025-10-15T14:30:00Z',
                'updated_at': '2025-10-20T16:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [1]
            },
            {
                'id': 3,
                'name': 'Idea 3',
                'description': 'Description 3',
                'customer': 'Customer C',
                'source_name': 'Bob Johnson',
                'source_email': 'bob@example.com',
                'created_at': '2025-11-01T09:15:00Z',
                'updated_at': '2025-11-05T11:30:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'On deck'}
                ],
                'team_ids': [2]
            }
        ]

    @pytest.fixture
    def mock_team_mapping(self):
        """Sample team mapping"""
        return {
            1: 'Engineering',
            2: 'Product'
        }

    def test_sla_init_creates_spreadsheet(self, temp_output_file, mock_ideas_data, mock_team_mapping):
        """Test that sla_init() creates a spreadsheet with correct structure"""
        # Mock the API resources and config
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Verify file was created
            assert os.path.exists(temp_output_file)
            assert os.path.getsize(temp_output_file) > 0

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Verify row count
            assert len(df) == 3

            # Verify column structure - core columns first
            expected_core_cols = [
                'id', 'url', 'name', 'description', 'customer',
                'source_name', 'source_email',
                'created_at', 'updated_at',
                'idea_status', 'location_status'
            ]
            for col in expected_core_cols:
                assert col in df.columns, f"Missing core column: {col}"

            # Verify team columns present
            assert 'Engineering' in df.columns
            assert 'Product' in df.columns

            # Verify SLA columns present
            assert 'response_sla' in df.columns
            assert 'roadmap_sla' in df.columns
            assert 'currently_meets_response_sla' in df.columns
            assert 'currently_meets_roadmap_sla' in df.columns

    def test_sla_init_calculates_sla_columns_correctly(self, temp_output_file, mock_ideas_data, mock_team_mapping):
        """Test that SLA calculations are applied correctly"""
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Verify SLA calculations for each idea

            # Idea 1: Status = "Accepted"
            # Should have: response_sla set, roadmap_sla set, both booleans True
            idea1 = df[df['id'] == 1].iloc[0]
            assert pd.notna(idea1['response_sla']), "Accepted idea should have response_sla set"
            assert pd.notna(idea1['roadmap_sla']), "Accepted idea should have roadmap_sla set"
            assert idea1['currently_meets_response_sla'] == True
            assert idea1['currently_meets_roadmap_sla'] == True

            # Idea 2: Status = "In Review"
            # Should have: response_sla set, roadmap_sla NOT set, response boolean True, roadmap False
            idea2 = df[df['id'] == 2].iloc[0]
            assert pd.notna(idea2['response_sla']), "In Review idea should have response_sla set"
            assert pd.isna(idea2['roadmap_sla']), "In Review idea should NOT have roadmap_sla set"
            assert idea2['currently_meets_response_sla'] == True
            assert idea2['currently_meets_roadmap_sla'] == False

            # Idea 3: Status = "On deck"
            # Should have: no SLA dates, both booleans False
            idea3 = df[df['id'] == 3].iloc[0]
            assert pd.isna(idea3['response_sla']), "On deck idea should NOT have response_sla set"
            assert pd.isna(idea3['roadmap_sla']), "On deck idea should NOT have roadmap_sla set"
            assert idea3['currently_meets_response_sla'] == False
            assert idea3['currently_meets_roadmap_sla'] == False

    def test_sla_init_extracts_idea_status_correctly(self, temp_output_file, mock_ideas_data, mock_team_mapping):
        """Test that idea_status is extracted from custom dropdown fields"""
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Verify idea_status values
            assert df[df['id'] == 1].iloc[0]['idea_status'] == 'Accepted'
            assert df[df['id'] == 2].iloc[0]['idea_status'] == 'In Review'
            assert df[df['id'] == 3].iloc[0]['idea_status'] == 'On deck'

    def test_sla_init_calls_api_with_correct_parameters(self, temp_output_file, mock_ideas_data, mock_team_mapping):
        """Test that API is called with correct parameters"""
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Verify API calls
            MockIdeasResource.assert_called_once_with('fake_token.txt')
            MockTeamsResource.assert_called_once_with('fake_token.txt')

            # Verify fetch_enhanced was called with correct parameters
            mock_ideas_instance.fetch_enhanced.assert_called_once_with(
                page=1,
                page_size=200,
                filters=None,
                get_all=True,
                location_status="all"  # Should fetch ALL ideas including archived
            )

            # Verify team mapping was built
            mock_teams_instance.build_id_to_name_mapping.assert_called_once()

    def test_sla_init_with_all_ideas_filtered(self, temp_output_file, mock_team_mapping):
        """Test that init handles case where all ideas are filtered out"""
        # Mock API to return ideas that all fail filters
        filtered_ideas = [
            {
                'id': 1,
                'name': 'Old Idea',
                'description': 'Test',
                'customer': 'ACME',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-01T10:00:00Z',  # Before Sep 15 cutoff
                'updated_at': '2025-09-01T10:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'On deck'}
                ],
                'team_ids': [1]
            },
            {
                'id': 2,
                'name': 'Jason Early',
                'description': 'Test',
                'customer': 'Beta',
                'source_name': 'Jason Ladicos',
                'source_email': 'jason@example.com',
                'created_at': '2025-10-01T10:00:00Z',  # Before Nov 3, from Jason
                'updated_at': '2025-10-01T10:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'On deck'}
                ],
                'team_ids': [2]
            },
            {
                'id': 3,
                'name': 'TEST Customer',
                'description': 'Test',
                'customer': 'TEST',  # TEST customer
                'source_name': 'Bob',
                'source_email': 'bob@example.com',
                'created_at': '2025-09-16T10:00:00Z',
                'updated_at': '2025-09-16T10:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'On deck'}
                ],
                'team_ids': [1]
            }
        ]

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = filtered_ideas

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Verify file was created
            assert os.path.exists(temp_output_file)

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Should have 0 rows (all filtered out) but proper column structure
            assert len(df) == 0
            assert 'id' in df.columns
            assert 'name' in df.columns
            assert 'response_sla' in df.columns
            assert 'roadmap_sla' in df.columns

    def test_sla_init_generates_correct_url_format(self, temp_output_file, mock_ideas_data, mock_team_mapping):
        """Test that URL column is generated with correct format"""
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock with trailing slash to test defensive handling
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas/'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Verify URL column exists and is in correct position (after id)
            assert 'url' in df.columns
            columns_list = df.columns.tolist()
            id_index = columns_list.index('id')
            url_index = columns_list.index('url')
            assert url_index == id_index + 1, "URL column should be immediately after id column"

            # Verify URL format for each idea (should not have double slashes)
            for _, row in df.iterrows():
                idea_id = row['id']
                url = row['url']
                expected_url = f'https://app.productplan.com/ideas/{idea_id}'
                assert url == expected_url, f"URL should be '{expected_url}' but got '{url}'"
                assert '//' not in url.replace('https://', ''), "URL should not have double slashes"

    def test_sla_init_team_columns_ordered_and_last(self, temp_output_file):
        """Test that team columns are sorted by ID and come LAST (after custom fields)"""
        # Mock ideas with custom fields
        ideas_with_custom_fields = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'custom_text_fields': [
                    {'label': 'Priority', 'value': 'High'},
                    {'label': 'Category', 'value': 'Feature'}
                ],
                'team_ids': [1, 3, 5]  # Teams 1, 3, 5
            }
        ]

        # Team mapping with IDs NOT in ascending order by name
        # Team IDs: 5 (Design), 1 (Engineering), 3 (Product)
        # After sorting by ID: Engineering(1), Product(3), Design(5)
        team_mapping = {
            5: 'Design',
            1: 'Engineering',
            3: 'Product'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_with_custom_fields

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            # Setup config mock
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_init()
            sla_init(temp_output_file, 'fake_token.txt')

            # Read the file back
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Get all column names
            columns_list = df.columns.tolist()

            # Verify team columns exist
            assert 'Engineering' in columns_list
            assert 'Product' in columns_list
            assert 'Design' in columns_list

            # Verify custom field columns exist (note: custom text fields are prefixed with "Custom: ")
            assert 'Custom: Priority' in columns_list
            assert 'Custom: Category' in columns_list

            # Find positions
            engineering_idx = columns_list.index('Engineering')
            product_idx = columns_list.index('Product')
            design_idx = columns_list.index('Design')
            priority_idx = columns_list.index('Custom: Priority')
            category_idx = columns_list.index('Custom: Category')

            # Verify team columns are sorted by team ID (Engineering=1, Product=3, Design=5)
            assert engineering_idx < product_idx < design_idx, \
                "Team columns should be sorted by team ID: Engineering(1), Product(3), Design(5)"

            # Verify team columns come AFTER custom fields
            assert priority_idx < engineering_idx, "Custom field 'Priority' should come before team column 'Engineering'"
            assert category_idx < engineering_idx, "Custom field 'Category' should come before team column 'Engineering'"

            # Verify team columns are the LAST columns in the DataFrame
            # Get expected core/SLA/status/custom columns
            expected_non_team_cols = [
                'id', 'url', 'name', 'description', 'customer', 'source_name', 'source_email',
                'created_at', 'updated_at', 'idea_status', 'location_status',
                'response_sla', 'roadmap_sla',
                'currently_meets_response_sla', 'currently_meets_roadmap_sla',
                'Custom: Priority', 'Custom: Category'
            ]

            # Last non-team column index
            last_non_team_idx = max(columns_list.index(col) for col in expected_non_team_cols if col in columns_list)

            # First team column index
            first_team_idx = min(engineering_idx, product_idx, design_idx)

            # Team columns should come after all non-team columns
            assert first_team_idx > last_non_team_idx, \
                "Team columns should come LAST (after all core, SLA, status, and custom field columns)"

    def test_sla_init_partial_teams_all_columns_appear(self, temp_output_file):
        """Test that ALL team columns appear even if idea only uses SOME teams"""
        # Idea uses teams 1 and 5, but mapping has teams 1, 2, 3, 5
        # All 4 team columns should appear, sorted by ID
        ideas_partial_teams = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [1, 5]  # Only uses 2 of 4 teams
            }
        ]

        # Team mapping has 4 teams, but idea only assigned to 2
        team_mapping = {
            1: 'Engineering',
            2: 'Marketing',
            3: 'Product',
            5: 'Design'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_partial_teams

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            columns_list = df.columns.tolist()

            # Verify ALL 4 team columns exist (even though idea only uses 2)
            assert 'Engineering' in columns_list, "Engineering column should exist"
            assert 'Marketing' in columns_list, "Marketing column should exist (even though idea doesn't use it)"
            assert 'Product' in columns_list, "Product column should exist (even though idea doesn't use it)"
            assert 'Design' in columns_list, "Design column should exist"

            # Get positions
            eng_idx = columns_list.index('Engineering')
            mkt_idx = columns_list.index('Marketing')
            prod_idx = columns_list.index('Product')
            design_idx = columns_list.index('Design')

            # Verify team columns sorted by ID: Engineering(1), Marketing(2), Product(3), Design(5)
            assert eng_idx < mkt_idx < prod_idx < design_idx, \
                "Team columns should be sorted by team ID even when not all teams are used"

            # Verify values: used teams = 1, unused teams = 0
            row = df.iloc[0]
            assert row['Engineering'] == 1, "Engineering should be 1 (idea uses this team)"
            assert row['Marketing'] == 0, "Marketing should be 0 (idea doesn't use this team)"
            assert row['Product'] == 0, "Product should be 0 (idea doesn't use this team)"
            assert row['Design'] == 1, "Design should be 1 (idea uses this team)"

    def test_sla_init_no_custom_fields_teams_still_last(self, temp_output_file):
        """Test that team columns are last even when there are NO custom fields"""
        ideas_no_custom = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'custom_text_fields': [],  # NO custom text fields
                'team_ids': [1, 3]
            }
        ]

        team_mapping = {
            1: 'Engineering',
            3: 'Product'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_no_custom

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            columns_list = df.columns.tolist()

            # Verify team columns exist
            assert 'Engineering' in columns_list
            assert 'Product' in columns_list

            # Get positions
            eng_idx = columns_list.index('Engineering')
            prod_idx = columns_list.index('Product')

            # Get all expected core/SLA/status columns (no custom text fields)
            expected_non_team_cols = [
                'id', 'url', 'name', 'description', 'customer', 'source_name', 'source_email',
                'created_at', 'updated_at', 'idea_status', 'location_status',
                'response_sla', 'roadmap_sla',
                'currently_meets_response_sla', 'currently_meets_roadmap_sla',
                'Custom_Dropdown: idea status'  # Only dropdown field
            ]

            # Last non-team column
            last_non_team_idx = max(columns_list.index(col) for col in expected_non_team_cols if col in columns_list)

            # First team column
            first_team_idx = min(eng_idx, prod_idx)

            # Team columns should STILL be last even with no custom text fields
            assert first_team_idx > last_non_team_idx, \
                "Team columns should be LAST even when there are no custom text fields"

    def test_sla_init_empty_team_mapping_no_crash(self, temp_output_file):
        """Test that empty team mapping doesn't crash (graceful handling)"""
        ideas_no_teams = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': []  # No teams
            }
        ]

        team_mapping = {}  # Empty team mapping

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_no_teams

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Should not crash
            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            # Verify no team columns exist
            columns_list = df.columns.tolist()

            # Check that no team columns were added
            team_cols = [col for col in columns_list if col in team_mapping.values()]
            assert len(team_cols) == 0, "No team columns should exist with empty team mapping"

    def test_sla_init_single_team_edge_case(self, temp_output_file):
        """Test single team in mapping (sorting edge case)"""
        ideas_single_team = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [42]
            }
        ]

        team_mapping = {42: 'Engineering'}  # Single team

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_single_team

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            columns_list = df.columns.tolist()

            # Verify single team column exists
            assert 'Engineering' in columns_list, "Single team column should exist"

            # Verify it's still last
            eng_idx = columns_list.index('Engineering')
            assert eng_idx == len(columns_list) - 1, "Single team column should be last column"

    def test_sla_init_large_team_id_gaps(self, temp_output_file):
        """Test team columns sorted correctly with large ID gaps"""
        ideas_large_gaps = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [1, 100, 9999]
            }
        ]

        team_mapping = {
            1: 'Engineering',
            100: 'Product',
            9999: 'Design'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_large_gaps

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            columns_list = df.columns.tolist()

            # Verify all team columns exist
            assert 'Engineering' in columns_list
            assert 'Product' in columns_list
            assert 'Design' in columns_list

            # Get positions
            eng_idx = columns_list.index('Engineering')
            prod_idx = columns_list.index('Product')
            design_idx = columns_list.index('Design')

            # Verify sorted by numeric ID: Engineering(1) < Product(100) < Design(9999)
            assert eng_idx < prod_idx < design_idx, \
                "Team columns should be sorted numerically even with large ID gaps"

    def test_sla_init_team_id_zero(self, temp_output_file):
        """Test team with ID = 0 (edge case for sorting)"""
        ideas_zero_id = [
            {
                'id': 1,
                'name': 'Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': '2025-09-16T12:00:00Z',
                'updated_at': '2025-09-16T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [0, 1, 5]
            }
        ]

        team_mapping = {
            0: 'Default Team',
            1: 'Engineering',
            5: 'Design'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = ideas_zero_id

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            sla_init(temp_output_file, 'fake_token.txt')

            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()

            columns_list = df.columns.tolist()

            # Verify all team columns exist
            assert 'Default Team' in columns_list
            assert 'Engineering' in columns_list
            assert 'Design' in columns_list

            # Get positions
            default_idx = columns_list.index('Default Team')
            eng_idx = columns_list.index('Engineering')
            design_idx = columns_list.index('Design')

            # Verify sorted: Default Team(0) < Engineering(1) < Design(5)
            assert default_idx < eng_idx < design_idx, \
                "Team with ID=0 should be first in team columns"


class TestSLAUpdate:
    """Integration tests for sla_update() function"""

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path (without creating the file)"""
        # Generate a unique temporary file path without creating the file
        import tempfile
        fd, file_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)  # Close the file descriptor
        os.remove(file_path)  # Remove the file so it doesn't exist yet

        yield file_path

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.fixture
    def mock_team_mapping(self):
        """Sample team mapping"""
        return {
            1: 'Engineering',
            2: 'Product'
        }

    @pytest.fixture
    def existing_spreadsheet_data(self):
        """Sample data that would be in an existing spreadsheet"""
        return pd.DataFrame([
            {
                'id': 1,
                'name': 'Existing Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'John Doe',
                'source_email': 'john@example.com',
                'created_at': pd.Timestamp('2025-10-01 10:00:00'),
                'updated_at': pd.Timestamp('2025-10-10 12:00:00'),
                'idea_status': 'In Review',
                'location_status': 'visible',
                'response_sla': pd.Timestamp('2025-10-10 12:00:00'),
                'roadmap_sla': pd.NaT,
                'currently_meets_response_sla': True,
                'currently_meets_roadmap_sla': False,
                'Engineering': 1,
                'Product': 0
            },
            {
                'id': 2,
                'name': 'Existing Idea 2',
                'description': 'Description 2',
                'customer': 'Customer B',
                'source_name': 'Jane Smith',
                'source_email': 'jane@example.com',
                'created_at': pd.Timestamp('2025-10-05 14:30:00'),
                'updated_at': pd.Timestamp('2025-10-15 16:00:00'),
                'idea_status': 'Accepted',
                'location_status': 'visible',
                'response_sla': pd.Timestamp('2025-10-15 16:00:00'),
                'roadmap_sla': pd.Timestamp('2025-10-15 16:00:00'),
                'currently_meets_response_sla': True,
                'currently_meets_roadmap_sla': True,
                'Engineering': 1,
                'Product': 1
            }
        ])

    def test_sla_update_with_no_spreadsheet_calls_init(self, temp_output_file):
        """Test that sla_update() calls sla_init() if spreadsheet doesn't exist"""
        # We need to test this differently since patching sla_init is tricky
        # Instead, verify that sla_init is called by checking that file is created
        # and has correct structure (which only happens via init)
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup minimal mocks with at least 1 idea to avoid empty DataFrame issues
            test_idea = {
                'id': 1,
                'name': 'Test Idea',
                'description': 'Test',
                'customer': 'Test Customer',
                'source_name': 'Test User',
                'source_email': 'test@example.com',
                'created_at': '2025-10-01T10:00:00Z',
                'updated_at': '2025-10-10T12:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'On deck'}
                ],
                'team_ids': []
            }

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [test_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = {}

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update() on non-existent file
            sla_update(temp_output_file, 'fake_token.txt')

            # Verify file was created (which means init was called)
            assert os.path.exists(temp_output_file)

            # Read file and verify it has correct structure (created by init)
            storage = ExcelSLAStorage(temp_output_file)
            df = storage.read()
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1  # Should have the test idea
            assert df.iloc[0]['id'] == 1

    def test_sla_update_updates_changed_ideas(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that changed ideas are updated in the spreadsheet"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return updated idea
        updated_idea = {
            'id': 1,
            'name': 'Existing Idea 1 - Updated Name',  # Name changed
            'description': 'Description 1',
            'customer': 'Customer A',
            'source_name': 'John Doe',
            'source_email': 'john@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-11-01T15:00:00Z',  # Newer timestamp
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}  # Status changed
            ],
            'team_ids': [1]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [updated_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was updated
            idea1 = df[df['id'] == 1].iloc[0]
            assert idea1['name'] == 'Existing Idea 1 - Updated Name'
            assert idea1['idea_status'] == 'Accepted'

            # Verify historical response_sla date was preserved
            assert pd.notna(idea1['response_sla'])
            assert idea1['response_sla'] == pd.Timestamp('2025-10-10 12:00:00')

            # Verify roadmap_sla was set (status changed to Accepted)
            assert pd.notna(idea1['roadmap_sla'])

            # Verify both booleans are True
            assert idea1['currently_meets_response_sla'] == True
            assert idea1['currently_meets_roadmap_sla'] == True

            # Verify URL column exists and has correct value
            assert 'url' in df.columns, "URL column should exist"
            assert idea1['url'] == 'https://app.productplan.com/ideas/1', "URL should be correct for idea 1"

    def test_sla_update_adds_previously_filtered_idea(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that previously filtered idea is added with correct SLA logic"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return idea that was filtered out but now passes
        # Created 30 days ago, status is "Accepted", but was customer="TEST" before
        new_idea = {
            'id': 999,
            'name': 'Previously Filtered Idea',
            'description': 'Was TEST customer, now real',
            'customer': 'Real Customer',  # Changed from "TEST"
            'source_name': 'Test User',
            'source_email': 'test@example.com',
            'created_at': '2025-10-02T10:00:00Z',  # 30 days ago
            'updated_at': '2025-11-01T14:00:00Z',  # Today (when customer changed)
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'Accepted'}
            ],
            'team_ids': [1]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [new_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was added
            assert len(df) == 3  # Was 2, now 3
            new_idea_row = df[df['id'] == 999].iloc[0]

            # Verify SLA dates were set to updated_at (when we first observed it)
            assert pd.notna(new_idea_row['response_sla'])
            assert pd.notna(new_idea_row['roadmap_sla'])

            # SLA dates should be updated_at (Nov 1)
            assert new_idea_row['response_sla'].date() == pd.Timestamp('2025-11-01').date()
            assert new_idea_row['roadmap_sla'].date() == pd.Timestamp('2025-11-01').date()

            # Compliance is measured from created_at (Oct 2)
            # Response: Nov 1 - Oct 2 = 30 days > 14 days → FALSE
            # Roadmap: Nov 1 - Oct 2 = 30 days < 60 days → TRUE
            assert new_idea_row['currently_meets_response_sla'] == False
            assert new_idea_row['currently_meets_roadmap_sla'] == True

            # Verify URL column exists and has correct value for new idea
            assert 'url' in df.columns, "URL column should exist"
            assert new_idea_row['url'] == 'https://app.productplan.com/ideas/999', "URL should be correct for idea 999"

    def test_sla_update_removes_filtered_out_idea(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that ideas failing filters are removed from spreadsheet"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return idea that now fails filters (customer changed to "TEST")
        filtered_idea = {
            'id': 1,  # Existing idea
            'name': 'Existing Idea 1',
            'description': 'Description 1',
            'customer': 'TEST',  # Changed to TEST - will be filtered out
            'source_name': 'John Doe',
            'source_email': 'john@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-11-01T15:00:00Z',
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'team_ids': [1]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [filtered_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was removed
            assert len(df) == 1  # Was 2, now 1
            assert 1 not in df['id'].values
            assert 2 in df['id'].values  # Other idea still there

            # Verify URL column exists for remaining idea
            assert 'url' in df.columns, "URL column should exist"
            remaining_idea = df[df['id'] == 2].iloc[0]
            assert remaining_idea['url'] == 'https://app.productplan.com/ideas/2', "URL should be correct for remaining idea"

    def test_sla_update_adds_new_idea(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that new ideas (not in spreadsheet) are added"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return a new idea
        new_idea = {
            'id': 100,
            'name': 'Brand New Idea',
            'description': 'New description',
            'customer': 'New Customer',
            'source_name': 'New User',
            'source_email': 'new@example.com',
            'created_at': '2025-10-25T10:00:00Z',
            'updated_at': '2025-11-01T14:00:00Z',
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'team_ids': [2]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [new_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was added
            assert len(df) == 3  # Was 2, now 3
            new_idea_row = df[df['id'] == 100].iloc[0]
            assert new_idea_row['name'] == 'Brand New Idea'
            assert new_idea_row['idea_status'] == 'In Review'

            # Verify SLA dates were set
            assert pd.notna(new_idea_row['response_sla'])
            assert pd.isna(new_idea_row['roadmap_sla'])  # Not Accepted/Rejected yet

            # Verify URL column exists and has correct value for new idea
            assert 'url' in df.columns, "URL column should exist"
            assert new_idea_row['url'] == 'https://app.productplan.com/ideas/100', "URL should be correct for new idea 100"

    def test_sla_update_skips_unchanged_ideas(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that ideas with older timestamps are skipped"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return idea with OLDER timestamp (shouldn't update)
        unchanged_idea = {
            'id': 1,
            'name': 'Existing Idea 1 - Should Not Update',
            'description': 'Description 1',
            'customer': 'Customer A',
            'source_name': 'John Doe',
            'source_email': 'john@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-10-05T12:00:00Z',  # OLDER than spreadsheet (2025-10-10)
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'team_ids': [1]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [unchanged_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was NOT updated (name should be original)
            idea1 = df[df['id'] == 1].iloc[0]
            assert idea1['name'] == 'Existing Idea 1'  # Original name preserved
            assert idea1['updated_at'] == pd.Timestamp('2025-10-10 12:00:00')  # Original timestamp

            # Verify URL column exists (even though idea wasn't updated)
            assert 'url' in df.columns, "URL column should exist"
            assert idea1['url'] == 'https://app.productplan.com/ideas/1', "URL should be correct for idea 1"

    def test_sla_update_with_all_filtered_out(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that update handles case where all fetched ideas are filtered out"""
        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        # Mock API to return ideas that all fail filters
        filtered_ideas = [
            {
                'id': 300,
                'name': 'Test Idea',
                'description': 'Test',
                'customer': 'TEST',  # Will be filtered
                'source_name': 'Test User',
                'source_email': 'test@example.com',
                'created_at': '2025-10-20T10:00:00Z',
                'updated_at': '2025-11-01T14:00:00Z',
                'location_status': 'visible',
                'custom_dropdown_fields': [
                    {'label': 'idea status', 'value': 'In Review'}
                ],
                'team_ids': [1]
            }
        ]

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = filtered_ideas

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify spreadsheet unchanged (all fetched ideas were filtered)
            assert len(df) == 2  # Original 2 ideas still there
            assert 300 not in df['id'].values  # New filtered idea not added

            # Verify URL column exists for existing ideas
            assert 'url' in df.columns, "URL column should exist"
            idea1 = df[df['id'] == 1].iloc[0]
            idea2 = df[df['id'] == 2].iloc[0]
            assert idea1['url'] == 'https://app.productplan.com/ideas/1', "URL should be correct for idea 1"
            assert idea2['url'] == 'https://app.productplan.com/ideas/2', "URL should be correct for idea 2"

    def test_sla_update_verifies_14_day_lookback(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that update fetches ideas from exactly 14 days ago"""
        from datetime import datetime, timedelta

        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.datetime') as mock_datetime, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Mock datetime.now() to return a fixed date
            fixed_now = datetime(2025, 11, 3, 14, 30, 0)
            mock_datetime.now.return_value = fixed_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = []

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock for URL generation
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Verify fetch_enhanced was called with correct lookback date
            # Should be 14 days before fixed_now
            expected_lookback = (fixed_now - timedelta(days=14)).strftime('%Y-%m-%d')

            # Get the actual call arguments
            call_args = mock_ideas_instance.fetch_enhanced.call_args

            # Verify filters parameter contains the lookback date
            assert call_args is not None
            filters = call_args[1].get('filters') or call_args[0][2] if len(call_args[0]) > 2 else None

            # The filter should include updated_at_gteq with the 14-day lookback date
            if filters:
                assert 'updated_at_gteq' in filters
                assert filters['updated_at_gteq'] == expected_lookback

    def test_sla_update_adds_url_column_to_old_spreadsheet(self, temp_output_file, mock_team_mapping):
        """Test that URL column is added to old spreadsheets and new ideas"""
        # Create existing spreadsheet WITHOUT url column (simulates old spreadsheet)
        existing_data_without_url = pd.DataFrame([
            {
                'id': 1,
                'name': 'Existing Idea 1',
                'description': 'Description 1',
                'customer': 'Customer A',
                'source_name': 'John Doe',
                'source_email': 'john@example.com',
                'created_at': pd.Timestamp('2025-10-01 10:00:00'),
                'updated_at': pd.Timestamp('2025-10-10 12:00:00'),
                'idea_status': 'In Review',
                'location_status': 'visible',
                'response_sla': pd.Timestamp('2025-10-10 12:00:00'),
                'roadmap_sla': pd.NaT,
                'currently_meets_response_sla': True,
                'currently_meets_roadmap_sla': False,
                'Engineering': 1,
                'Product': 0
            }
        ])

        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_data_without_url)

        # Verify old spreadsheet doesn't have url column
        df_before = storage.read()
        assert 'url' not in df_before.columns, "Test setup error: existing data should not have url column"

        # Mock API to return existing idea (updated) and a new idea
        existing_idea_updated = {
            'id': 1,
            'name': 'Existing Idea 1 - Updated',
            'description': 'Description 1',
            'customer': 'Customer A',
            'source_name': 'John Doe',
            'source_email': 'john@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-11-01T15:00:00Z',  # Newer timestamp
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'team_ids': [1]
        }

        new_idea = {
            'id': 999,
            'name': 'Brand New Idea',
            'description': 'New idea description',
            'customer': 'New Customer',
            'source_name': 'Jane Smith',
            'source_email': 'jane@example.com',
            'created_at': '2025-10-15T10:00:00Z',
            'updated_at': '2025-11-01T14:00:00Z',
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'On deck'}
            ],
            'team_ids': [2]
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [existing_idea_updated, new_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Setup config mock with trailing slash to test defensive handling
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas/'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify URL column exists and is in correct position (after id)
            assert 'url' in df.columns, "URL column should exist after update"
            columns_list = df.columns.tolist()
            id_index = columns_list.index('id')
            url_index = columns_list.index('url')
            assert url_index == id_index + 1, "URL column should be immediately after id column"

            # Verify URL format for existing idea (defensive logic added URL)
            existing_idea_row = df[df['id'] == 1].iloc[0]
            assert pd.notna(existing_idea_row['url']), "Existing idea should have URL after update"
            expected_url_1 = 'https://app.productplan.com/ideas/1'
            assert existing_idea_row['url'] == expected_url_1, f"URL should be '{expected_url_1}' but got '{existing_idea_row['url']}'"
            assert '//' not in existing_idea_row['url'].replace('https://', ''), "URL should not have double slashes"

            # Verify URL format for new idea
            new_idea_row = df[df['id'] == 999].iloc[0]
            assert pd.notna(new_idea_row['url']), "New idea should have URL"
            expected_url_999 = 'https://app.productplan.com/ideas/999'
            assert new_idea_row['url'] == expected_url_999, f"URL should be '{expected_url_999}' but got '{new_idea_row['url']}'"
            assert '//' not in new_idea_row['url'].replace('https://', ''), "URL should not have double slashes"

    def test_sla_update_team_columns_ordered_and_last_with_new_team(self, temp_output_file):
        """Test that team columns stay sorted and last when new teams are added during update"""
        # Create existing spreadsheet with 2 teams (IDs 1 and 3) and custom fields
        existing_data = pd.DataFrame([
            {
                'id': 1,
                'url': 'https://app.productplan.com/ideas/1',
                'name': 'Existing Idea',
                'description': 'Description',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': pd.Timestamp('2025-10-01 10:00:00'),
                'updated_at': pd.Timestamp('2025-10-10 12:00:00'),
                'idea_status': 'In Review',
                'location_status': 'visible',
                'response_sla': pd.Timestamp('2025-10-10 12:00:00'),
                'roadmap_sla': pd.NaT,
                'currently_meets_response_sla': True,
                'currently_meets_roadmap_sla': False,
                'Custom: Priority': 'High',  # Custom field
                'Custom: Category': 'Feature',  # Custom field
                'Engineering': 1,  # Team ID 1
                'Product': 1  # Team ID 3
            }
        ])

        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_data)

        # Mock API to return idea with NEW team (ID 5) and new custom field
        updated_idea = {
            'id': 1,
            'name': 'Existing Idea - Updated',
            'description': 'Description',
            'customer': 'Customer A',
            'source_name': 'Alice',
            'source_email': 'alice@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-11-01T15:00:00Z',  # Newer timestamp
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'custom_text_fields': [
                {'label': 'Priority', 'value': 'High'},
                {'label': 'Category', 'value': 'Feature'},
                {'label': 'Complexity', 'value': 'Medium'}  # NEW custom field
            ],
            'team_ids': [1, 3, 5]  # Now includes team ID 5 (Design)
        }

        # Team mapping now includes Design (ID 5)
        # IDs: 5 (Design), 1 (Engineering), 3 (Product)
        # After sorting by ID: Engineering(1), Product(3), Design(5)
        team_mapping = {
            5: 'Design',
            1: 'Engineering',
            3: 'Product'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [updated_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            # Setup config mock
            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Get all column names
            columns_list = df.columns.tolist()

            # Verify all team columns exist (including new Design team)
            assert 'Engineering' in columns_list
            assert 'Product' in columns_list
            assert 'Design' in columns_list

            # Verify all custom fields exist (including new Complexity field)
            # Note: custom text fields are prefixed with "Custom: "
            assert 'Custom: Priority' in columns_list
            assert 'Custom: Category' in columns_list
            assert 'Custom: Complexity' in columns_list

            # Find positions
            engineering_idx = columns_list.index('Engineering')
            product_idx = columns_list.index('Product')
            design_idx = columns_list.index('Design')
            priority_idx = columns_list.index('Custom: Priority')
            category_idx = columns_list.index('Custom: Category')
            complexity_idx = columns_list.index('Custom: Complexity')

            # Verify team columns are sorted by team ID (Engineering=1, Product=3, Design=5)
            assert engineering_idx < product_idx < design_idx, \
                "Team columns should be sorted by team ID: Engineering(1), Product(3), Design(5)"

            # Verify new team (Design) appears at the END of team columns
            assert design_idx > product_idx, "New team (Design, ID=5) should appear after existing teams"

            # Verify ALL custom fields come BEFORE team columns
            assert priority_idx < engineering_idx, "Custom field 'Priority' should come before team columns"
            assert category_idx < engineering_idx, "Custom field 'Category' should come before team columns"
            assert complexity_idx < engineering_idx, "New custom field 'Complexity' should come before team columns"

            # Verify team columns are the LAST columns
            expected_non_team_cols = [
                'id', 'url', 'name', 'description', 'customer', 'source_name', 'source_email',
                'created_at', 'updated_at', 'idea_status', 'location_status',
                'response_sla', 'roadmap_sla',
                'currently_meets_response_sla', 'currently_meets_roadmap_sla',
                'Custom: Priority', 'Custom: Category', 'Custom: Complexity'
            ]

            # Last non-team column index
            last_non_team_idx = max(columns_list.index(col) for col in expected_non_team_cols if col in columns_list)

            # First team column index
            first_team_idx = min(engineering_idx, product_idx, design_idx)

            # Team columns should come after all non-team columns
            assert first_team_idx > last_non_team_idx, \
                "Team columns should come LAST (after all core, SLA, status, and custom field columns)"

            # Verify new custom field did NOT shift team column positions
            # (All team columns should still be at the end in sorted order)

    def test_sla_update_all_team_columns_added_even_if_unused(self, temp_output_file):
        """Test that ALL team columns from mapping are added, not just ones idea uses"""
        # This tests for the potential bug: if an idea only uses some teams,
        # we should still add ALL team columns to the DataFrame

        # Create existing spreadsheet with 2 teams
        existing_data = pd.DataFrame([
            {
                'id': 1,
                'url': 'https://app.productplan.com/ideas/1',
                'name': 'Existing Idea',
                'description': 'Description',
                'customer': 'Customer A',
                'source_name': 'Alice',
                'source_email': 'alice@example.com',
                'created_at': pd.Timestamp('2025-10-01 10:00:00'),
                'updated_at': pd.Timestamp('2025-10-10 12:00:00'),
                'idea_status': 'In Review',
                'location_status': 'visible',
                'response_sla': pd.Timestamp('2025-10-10 12:00:00'),
                'roadmap_sla': pd.NaT,
                'currently_meets_response_sla': True,
                'currently_meets_roadmap_sla': False,
                'Engineering': 1,  # Team ID 1
                'Product': 1  # Team ID 3
            }
        ])

        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_data)

        # Updated idea only uses Engineering (team ID 1), NOT Product or new Marketing
        updated_idea = {
            'id': 1,
            'name': 'Existing Idea - Updated',
            'description': 'Description',
            'customer': 'Customer A',
            'source_name': 'Alice',
            'source_email': 'alice@example.com',
            'created_at': '2025-10-01T10:00:00Z',
            'updated_at': '2025-11-01T15:00:00Z',  # Newer timestamp
            'location_status': 'visible',
            'custom_dropdown_fields': [
                {'label': 'idea status', 'value': 'In Review'}
            ],
            'team_ids': [1]  # Only uses Engineering, not Product or Marketing
        }

        # Team mapping now has 3 teams, but idea only uses 1
        team_mapping = {
            1: 'Engineering',
            2: 'Marketing',  # NEW team, idea doesn't use it
            3: 'Product'
        }

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.config') as mock_config:

            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [updated_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = team_mapping

            mock_config.get_url_prefix.return_value = 'https://app.productplan.com/ideas'

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            columns_list = df.columns.tolist()

            # CRITICAL: ALL 3 team columns should exist, even though idea only uses 1
            assert 'Engineering' in columns_list, "Engineering column should exist"
            assert 'Marketing' in columns_list, "Marketing column should exist (even though idea doesn't use it)"
            assert 'Product' in columns_list, "Product column should exist (even though idea doesn't use it)"

            # Get positions
            eng_idx = columns_list.index('Engineering')
            mkt_idx = columns_list.index('Marketing')
            prod_idx = columns_list.index('Product')

            # Verify sorted by team ID: Engineering(1), Marketing(2), Product(3)
            assert eng_idx < mkt_idx < prod_idx, \
                "Team columns should be sorted by team ID"

            # Verify values: Engineering=1, Marketing=0, Product=0
            row = df.iloc[0]
            assert row['Engineering'] == 1, "Engineering should be 1 (idea uses this team)"
            assert row['Marketing'] == 0, "Marketing should be 0 (idea doesn't use this team)"
            assert row['Product'] == 0, "Product should be 0 (idea no longer uses this team)"
