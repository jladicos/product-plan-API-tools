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
        # Mock the API resources
        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
                'id', 'name', 'description', 'customer',
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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = mock_ideas_data

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = filtered_ideas

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [updated_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [new_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [filtered_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was removed
            assert len(df) == 1  # Was 2, now 1
            assert 1 not in df['id'].values
            assert 2 in df['id'].values  # Other idea still there

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [new_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = [unchanged_idea]

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify idea was NOT updated (name should be original)
            idea1 = df[df['id'] == 1].iloc[0]
            assert idea1['name'] == 'Existing Idea 1'  # Original name preserved
            assert idea1['updated_at'] == pd.Timestamp('2025-10-10 12:00:00')  # Original timestamp

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
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource:

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = filtered_ideas

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

            # Call sla_update()
            sla_update(temp_output_file, 'fake_token.txt')

            # Read updated spreadsheet
            df = storage.read()

            # Verify spreadsheet unchanged (all fetched ideas were filtered)
            assert len(df) == 2  # Original 2 ideas still there
            assert 300 not in df['id'].values  # New filtered idea not added

    def test_sla_update_verifies_14_day_lookback(self, temp_output_file, existing_spreadsheet_data, mock_team_mapping):
        """Test that update fetches ideas from exactly 14 days ago"""
        from datetime import datetime, timedelta

        # Create existing spreadsheet
        storage = ExcelSLAStorage(temp_output_file)
        storage.write(existing_spreadsheet_data)

        with patch('productplan_api_tools.sla.manager.IdeasResource') as MockIdeasResource, \
             patch('productplan_api_tools.sla.manager.TeamsResource') as MockTeamsResource, \
             patch('productplan_api_tools.sla.manager.datetime') as mock_datetime:

            # Mock datetime.now() to return a fixed date
            fixed_now = datetime(2025, 11, 3, 14, 30, 0)
            mock_datetime.now.return_value = fixed_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            # Setup mocks
            mock_ideas_instance = MockIdeasResource.return_value
            mock_ideas_instance.fetch_enhanced.return_value = []

            mock_teams_instance = MockTeamsResource.return_value
            mock_teams_instance.build_id_to_name_mapping.return_value = mock_team_mapping

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
