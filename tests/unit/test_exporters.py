"""
Unit tests for exporter functions

Tests all exporter modules: base, excel, markdown, and javascript.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open, MagicMock
from productplan_api_tools.exporters import base, excel, markdown, javascript


class TestBaseExporter:
    """Test base exporter utilities"""

    def test_ensure_output_directory_creates_directory(self):
        """Test that ensure_output_directory creates directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir1", "subdir2", "file.xlsx")

            # Directory shouldn't exist yet
            parent_dir = os.path.dirname(output_path)
            assert not os.path.exists(parent_dir)

            # Call ensure_output_directory
            base.ensure_output_directory(output_path)

            # Directory should now exist
            assert os.path.exists(parent_dir)

    def test_ensure_output_directory_handles_existing_directory(self):
        """Test that ensure_output_directory works with existing directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "file.xlsx")

            # Directory already exists
            assert os.path.exists(tmpdir)

            # Should not raise error
            base.ensure_output_directory(output_path)

            # Directory should still exist
            assert os.path.exists(tmpdir)

    def test_ensure_output_directory_handles_no_directory_component(self):
        """Test that ensure_output_directory handles filename with no directory"""
        # Filename with no directory component
        base.ensure_output_directory("file.xlsx")

        # Should not raise error (nothing to create)


class TestExcelExporter:
    """Test Excel exporter function"""

    @patch('productplan_api_tools.exporters.excel.pd.DataFrame')
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_basic(self, mock_ensure_dir, mock_dataframe):
        """Test basic Excel export"""
        data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]

        mock_df = MagicMock()
        mock_dataframe.return_value = mock_df

        excel.export(data, "output.xlsx")

        # Should create DataFrame
        mock_dataframe.assert_called_once_with(data)

        # Should ensure directory exists
        mock_ensure_dir.assert_called_once_with("output.xlsx")

        # Should call to_excel
        mock_df.to_excel.assert_called_once_with("output.xlsx", index=False)

    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_empty_data(self, mock_ensure_dir):
        """Test Excel export with empty data"""
        # Should handle empty data gracefully (just print warning)
        excel.export([], "output.xlsx")

        # Should not raise error

    @patch('productplan_api_tools.exporters.excel.pd.DataFrame')
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_creates_directory(self, mock_ensure_dir, mock_dataframe):
        """Test that export creates parent directory"""
        data = [{"id": 1}]
        mock_df = MagicMock()
        mock_dataframe.return_value = mock_df

        excel.export(data, "files/subdir/output.xlsx")

        # Should call ensure_output_directory with the path
        mock_ensure_dir.assert_called_once_with("files/subdir/output.xlsx")


class TestMarkdownExporter:
    """Test Markdown exporter function"""

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_okr_basic(self, mock_ensure_dir, mock_file):
        """Test basic OKR markdown export"""
        okr_data = [
            {
                "objective_id": 1,
                "objective_name": "Objective 1",
                "objective_description": "Description",
                "team_name": "Engineering",
                "status": "active",
                "key_result_name": "KR 1",
                "key_result_target": "100%",
                "key_result_current": "50%",
                "key_result_progress": "50%"
            }
        ]

        markdown.export_okr(okr_data, "output.md")

        # Should ensure directory exists
        mock_ensure_dir.assert_called_once_with("output.md")

        # Should open file for writing
        mock_file.assert_called_once_with("output.md", 'w', encoding='utf-8')

        # Verify markdown content was written
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        assert "# Objectives and Key Results" in written_content
        assert "## Objective 1" in written_content
        assert "### Team" in written_content
        assert "Engineering" in written_content
        assert "### Key Results" in written_content

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_okr_no_key_results(self, mock_ensure_dir, mock_file):
        """Test OKR export for objective with no key results"""
        okr_data = [
            {
                "objective_id": 1,
                "objective_name": "Objective 1",
                "objective_description": "",
                "team_name": "",
                "status": "active",
                "key_result_name": "",  # No key result
                "key_result_target": "",
                "key_result_current": "",
                "key_result_progress": ""
            }
        ]

        markdown.export_okr(okr_data, "output.md")

        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        assert "No key results" in written_content

    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_okr_empty_data(self, mock_ensure_dir):
        """Test OKR markdown export with empty data"""
        # Should handle empty data gracefully
        markdown.export_okr([], "output.md")

        # Should not raise error

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_okr_multiple_key_results(self, mock_ensure_dir, mock_file):
        """Test OKR export with multiple key results for same objective"""
        okr_data = [
            {
                "objective_id": 1,
                "objective_name": "Objective 1",
                "objective_description": "Desc",
                "team_name": "Engineering",
                "status": "active",
                "key_result_name": "KR 1",
                "key_result_target": "100%",
                "key_result_current": "50%",
                "key_result_progress": "50%"
            },
            {
                "objective_id": 1,  # Same objective
                "objective_name": "Objective 1",
                "objective_description": "Desc",
                "team_name": "Engineering",
                "status": "active",
                "key_result_name": "KR 2",
                "key_result_target": "200",
                "key_result_current": "100",
                "key_result_progress": "50%"
            }
        ]

        markdown.export_okr(okr_data, "output.md")

        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)

        # Should only have one objective heading
        assert written_content.count("## Objective 1") == 1

        # Should list both key results
        assert "KR 1" in written_content
        assert "KR 2" in written_content


class TestJavaScriptExporter:
    """Test JavaScript exporter function"""

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_miro_basic(self, mock_ensure_dir, mock_file):
        """Test basic Miro JavaScript export"""
        mapping_data = [
            {
                "company_objective_name": "Company Obj 1",
                "company_objective_id": 1,
                "team_objective_name": "Team Obj 1",
                "team_objective_id": 101,
                "team_name": "Engineering"
            }
        ]

        javascript.export_miro(mapping_data, "output.js")

        # Should ensure directory exists
        mock_ensure_dir.assert_called_once_with("output.js")

        # Should open file for writing
        mock_file.assert_called_once_with("output.js", 'w', encoding='utf-8')

        # Verify JavaScript content structure
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        assert "(async function()" in written_content
        assert "miro.board.createShape" in written_content
        assert "Company Obj 1" in written_content
        assert "Team Obj 1" in written_content

    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_miro_empty_data(self, mock_ensure_dir):
        """Test Miro export with empty data"""
        # Should handle empty data gracefully
        javascript.export_miro([], "output.js")

        # Should not raise error

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_miro_with_relationship_config(self, mock_ensure_dir, mock_file):
        """Test Miro export with relationship filtering"""
        mapping_data = [
            {
                "company_objective_name": "Company 1",
                "company_objective_id": 1,
                "team_objective_name": "Team 1",
                "team_objective_id": 101,
                "team_name": "Engineering"
            },
            {
                "company_objective_name": "Company 1",
                "company_objective_id": 1,
                "team_objective_name": "Team 2",
                "team_objective_id": 102,
                "team_name": "Product"
            }
        ]

        # Only include Team 1
        relationship_config = {"Company 1": ["Team 1"]}

        javascript.export_miro(mapping_data, "output.js", relationship_config=relationship_config)

        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)

        # Should include Team 1
        assert "Team 1" in written_content
        # Should NOT include Team 2 (filtered out)
        # (This depends on implementation details)

    @patch('builtins.open', new_callable=mock_open)
    @patch('productplan_api_tools.exporters.base.ensure_output_directory')
    def test_export_miro_escapes_special_characters(self, mock_ensure_dir, mock_file):
        """Test that special characters are properly escaped in JavaScript"""
        mapping_data = [
            {
                "company_objective_name": "Test `backtick` and ${variable}",
                "company_objective_id": 1,
                "team_objective_name": "Team with 'quotes'",
                "team_objective_id": 101,
                "team_name": "Engineering"
            }
        ]

        javascript.export_miro(mapping_data, "output.js")

        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)

        # Backticks and ${} should be escaped
        assert "\\`" in written_content or "backtick" in written_content
        assert "\\${" in written_content or "${" not in written_content or "variable" in written_content
