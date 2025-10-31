"""
Unit tests for utils module

Tests all utility functions for parsing and processing data.
"""

import pytest
import json
from productplan_api_tools import utils


class TestParseCustomTextFields:
    """Test parse_custom_text_fields() function"""

    def test_parse_json_string(self):
        """Test parsing JSON string"""
        json_str = '[{"label": "Problem", "value": "Auth issue"}]'
        result = utils.parse_custom_text_fields(json_str)

        assert len(result) == 1
        assert result[0]["label"] == "Problem"
        assert result[0]["value"] == "Auth issue"

    def test_parse_list_input(self):
        """Test parsing list input"""
        list_input = [{"label": "Problem", "value": "Issue"}]
        result = utils.parse_custom_text_fields(list_input)

        assert result == list_input

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = utils.parse_custom_text_fields("")

        assert result == []

    def test_parse_none(self):
        """Test parsing None"""
        result = utils.parse_custom_text_fields(None)

        assert result == []

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        invalid_json = "not valid json"
        result = utils.parse_custom_text_fields(invalid_json)

        # Should return empty list and not raise exception
        assert result == []

    def test_parse_complex_json(self):
        """Test parsing complex JSON with multiple fields"""
        json_str = json.dumps([
            {"label": "Field 1", "value": "Value 1"},
            {"label": "Field 2", "value": "Value 2"},
            {"label": "Field 3", "value": "Value 3"}
        ])
        result = utils.parse_custom_text_fields(json_str)

        assert len(result) == 3
        assert result[1]["label"] == "Field 2"


class TestParseCustomDropdownFields:
    """Test parse_custom_dropdown_fields() function"""

    def test_parse_list_input(self):
        """Test parsing list input"""
        list_input = [{"label": "Priority", "value": "High"}]
        result = utils.parse_custom_dropdown_fields(list_input)

        assert result == list_input

    def test_parse_none(self):
        """Test parsing None"""
        result = utils.parse_custom_dropdown_fields(None)

        assert result == []

    def test_parse_non_list(self):
        """Test parsing non-list input"""
        result = utils.parse_custom_dropdown_fields("string")

        assert result == []


class TestParseTeamIds:
    """Test parse_team_ids() function"""

    def test_parse_list_of_ints(self):
        """Test parsing list of integers"""
        team_ids = [1, 2, 3]
        result = utils.parse_team_ids(team_ids)

        assert result == [1, 2, 3]

    def test_parse_comma_separated_string(self):
        """Test parsing comma-separated string"""
        team_ids = "1, 2, 3"
        result = utils.parse_team_ids(team_ids)

        assert result == [1, 2, 3]

    def test_parse_comma_separated_with_extra_spaces(self):
        """Test parsing comma-separated string with extra whitespace"""
        team_ids = " 1 ,  2  , 3 "
        result = utils.parse_team_ids(team_ids)

        assert result == [1, 2, 3]

    def test_parse_none(self):
        """Test parsing None"""
        result = utils.parse_team_ids(None)

        assert result == []

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = utils.parse_team_ids("")

        assert result == []

    def test_parse_invalid_string(self):
        """Test parsing invalid string"""
        result = utils.parse_team_ids("not,numbers,here")

        # Should return empty list and not raise exception
        assert result == []


class TestAddCustomFieldColumns:
    """Test add_custom_field_columns() function"""

    def test_add_columns_basic(self):
        """Test adding custom field columns"""
        idea = {
            "id": 1,
            "name": "Test Idea",
            "custom_text_fields": '[{"label": "Problem", "value": "Issue"}]'
        }
        field_labels = {"Problem", "Solution"}

        result = utils.add_custom_field_columns(idea, field_labels)

        assert "Custom: Problem" in result
        assert result["Custom: Problem"] == "Issue"
        assert "Custom: Solution" in result
        assert result["Custom: Solution"] == ""  # Not in idea's fields

    def test_add_columns_empty_labels(self):
        """Test with empty field labels"""
        idea = {"id": 1}
        field_labels = set()

        result = utils.add_custom_field_columns(idea, field_labels)

        # Should just return copy of idea
        assert result["id"] == 1

    def test_add_columns_list_format(self):
        """Test with list format custom fields"""
        idea = {
            "id": 1,
            "custom_text_fields": [{"label": "Field1", "value": "Value1"}]
        }
        field_labels = {"Field1"}

        result = utils.add_custom_field_columns(idea, field_labels)

        assert result["Custom: Field1"] == "Value1"

    def test_add_columns_missing_custom_fields(self):
        """Test with idea missing custom_text_fields"""
        idea = {"id": 1}
        field_labels = {"Problem"}

        result = utils.add_custom_field_columns(idea, field_labels)

        # Should create empty column
        assert result["Custom: Problem"] == ""


class TestAddCustomDropdownColumns:
    """Test add_custom_dropdown_columns() function"""

    def test_add_dropdown_columns_basic(self):
        """Test adding custom dropdown columns"""
        idea = {
            "id": 1,
            "custom_dropdown_fields": [{"label": "Priority", "value": "High"}]
        }
        field_labels = {"Priority", "Status"}

        result = utils.add_custom_dropdown_columns(idea, field_labels)

        assert "Custom_Dropdown: Priority" in result
        assert result["Custom_Dropdown: Priority"] == "High"
        assert "Custom_Dropdown: Status" in result
        assert result["Custom_Dropdown: Status"] == ""

    def test_add_dropdown_columns_empty_labels(self):
        """Test with empty field labels"""
        idea = {"id": 1}
        field_labels = set()

        result = utils.add_custom_dropdown_columns(idea, field_labels)

        assert result["id"] == 1


class TestAddTeamColumns:
    """Test add_team_columns() function"""

    def test_add_team_columns_basic(self):
        """Test adding team columns"""
        idea = {
            "id": 1,
            "team_ids": [10, 20]
        }
        team_mapping = {
            10: "Engineering",
            20: "Product",
            30: "Design"
        }

        result = utils.add_team_columns(idea, team_mapping)

        assert result["Engineering"] == 1
        assert result["Product"] == 1
        assert result["Design"] == 0

    def test_add_team_columns_no_teams(self):
        """Test with idea assigned to no teams"""
        idea = {
            "id": 1,
            "team_ids": []
        }
        team_mapping = {10: "Engineering", 20: "Product"}

        result = utils.add_team_columns(idea, team_mapping)

        assert result["Engineering"] == 0
        assert result["Product"] == 0

    def test_add_team_columns_string_team_ids(self):
        """Test with team_ids as comma-separated string"""
        idea = {
            "id": 1,
            "team_ids": "10, 20"
        }
        team_mapping = {10: "Engineering", 20: "Product"}

        result = utils.add_team_columns(idea, team_mapping)

        assert result["Engineering"] == 1
        assert result["Product"] == 1


class TestProcessIdeas:
    """Test process_ideas() function"""

    def test_process_ideas_basic(self):
        """Test basic ideas processing"""
        ideas = [
            {
                "id": 1,
                "name": "Idea 1",
                "custom_text_fields": '[{"label": "Problem", "value": "Issue1"}]',
                "custom_dropdown_fields": [{"label": "Priority", "value": "High"}],
                "team_ids": [10]
            },
            {
                "id": 2,
                "name": "Idea 2",
                "custom_text_fields": '[{"label": "Problem", "value": "Issue2"}]',
                "custom_dropdown_fields": [{"label": "Priority", "value": "Low"}],
                "team_ids": [20]
            }
        ]
        team_mapping = {10: "Engineering", 20: "Product"}

        result = utils.process_ideas(ideas, team_mapping)

        assert len(result) == 2

        # Check custom text field columns
        assert result[0]["Custom: Problem"] == "Issue1"
        assert result[1]["Custom: Problem"] == "Issue2"

        # Check custom dropdown columns
        assert result[0]["Custom_Dropdown: Priority"] == "High"
        assert result[1]["Custom_Dropdown: Priority"] == "Low"

        # Check team columns
        assert result[0]["Engineering"] == 1
        assert result[0]["Product"] == 0
        assert result[1]["Engineering"] == 0
        assert result[1]["Product"] == 1

    def test_process_ideas_empty_list(self):
        """Test processing empty ideas list"""
        result = utils.process_ideas([], {})

        assert result == []

    def test_process_ideas_no_custom_fields(self):
        """Test processing ideas without custom fields"""
        ideas = [{"id": 1, "name": "Idea 1", "team_ids": []}]
        team_mapping = {10: "Engineering"}

        result = utils.process_ideas(ideas, team_mapping)

        assert len(result) == 1
        assert result[0]["id"] == 1
        # Should still have team columns
        assert result[0]["Engineering"] == 0


class TestProcessIdeaForms:
    """Test process_idea_forms() function"""

    def test_process_idea_forms_basic(self):
        """Test basic idea forms processing"""
        forms = [
            {
                "id": 1,
                "title": "Form 1",
                "custom_text_fields": [
                    {"label": "Question 1", "required": True}
                ],
                "custom_dropdown_fields": [
                    {"label": "Priority", "allowed_values": ["High", "Low"]}
                ]
            }
        ]

        result = utils.process_idea_forms(forms)

        assert len(result) == 1
        assert result[0]["Custom_Text_Field_1_Label"] == "Question 1"
        assert result[0]["Custom_Text_Field_1_required"] == True
        assert result[0]["Custom_Dropdown_Field_1_Label"] == "Priority"
        assert result[0]["Custom_Dropdown_Field_1_Allowed_Values"] == "High, Low"

        # Original nested fields should be removed
        assert "custom_text_fields" not in result[0]
        assert "custom_dropdown_fields" not in result[0]

    def test_process_idea_forms_empty_list(self):
        """Test processing empty forms list"""
        result = utils.process_idea_forms([])

        assert result == []

    def test_process_idea_forms_no_custom_fields(self):
        """Test processing forms without custom fields"""
        forms = [{"id": 1, "title": "Form 1"}]

        result = utils.process_idea_forms(forms)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["title"] == "Form 1"

    def test_process_idea_forms_multiple_fields(self):
        """Test processing forms with multiple custom fields"""
        forms = [
            {
                "id": 1,
                "custom_text_fields": [
                    {"label": "Q1"},
                    {"label": "Q2"},
                    {"label": "Q3"}
                ]
            }
        ]

        result = utils.process_idea_forms(forms)

        assert "Custom_Text_Field_1_Label" in result[0]
        assert "Custom_Text_Field_2_Label" in result[0]
        assert "Custom_Text_Field_3_Label" in result[0]
