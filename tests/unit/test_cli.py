"""
Unit tests for CLI module

Tests argument parsing, command routing, and handler functions.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from argparse import Namespace
from productplan_api_tools import cli


class TestParseArguments:
    """Test parse_arguments() function"""

    def test_parse_arguments_defaults(self):
        """Test that default arguments are set correctly"""
        with patch('sys.argv', ['script.py']):
            args = cli.parse_arguments()

            assert args.endpoint == 'ideas'
            assert args.token_file == 'token.txt'
            assert args.page == 1
            assert args.page_size == 200
            assert args.output == 'files/productplan_data.xlsx'
            assert args.all_pages is False
            assert args.location_status == 'not_archived'
            assert args.objective_status == 'active'
            assert args.output_format == 'excel'

    def test_parse_arguments_custom_values(self):
        """Test parsing custom argument values"""
        with patch('sys.argv', [
            'script.py',
            '--endpoint', 'okrs',
            '--page', '5',
            '--page-size', '500',
            '--output', 'custom.xlsx',
            '--all-pages',
            '--objective-status', 'all',
            '--output-format', 'markdown'
        ]):
            args = cli.parse_arguments()

            assert args.endpoint == 'okrs'
            assert args.page == 5
            assert args.page_size == 500
            assert args.output == 'custom.xlsx'
            assert args.all_pages is True
            assert args.objective_status == 'all'
            assert args.output_format == 'markdown'

    def test_parse_arguments_filters(self):
        """Test parsing filter arguments"""
        with patch('sys.argv', [
            'script.py',
            '--filter', 'name', 'Test',
            '--filter', 'status', 'active'
        ]):
            args = cli.parse_arguments()

            assert args.filter == [['name', 'Test'], ['status', 'active']]


class TestHandleIdeasCommand:
    """Test handle_ideas_command() function"""

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.utils')
    @patch('productplan_api_tools.cli.IdeasResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_ideas_basic(self, mock_teams_res_class, mock_ideas_res_class, mock_utils, mock_excel):
        """Test basic ideas command handling"""
        # Mock resource instances
        mock_ideas_res = Mock()
        mock_teams_res = Mock()
        mock_ideas_res_class.return_value = mock_ideas_res
        mock_teams_res_class.return_value = mock_teams_res

        # Mock data
        mock_ideas_res.fetch_enhanced.return_value = [{"id": 1, "name": "Idea 1"}]
        mock_teams_res.build_id_to_name_mapping.return_value = {10: "Engineering"}
        mock_utils.process_ideas.return_value = [{"id": 1, "name": "Idea 1", "Engineering": 1}]

        # Create args
        args = Namespace(
            output='output.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            location_status='not_archived'
        )

        cli.handle_ideas_command(args, "token.txt")

        # Verify resources were created
        mock_ideas_res_class.assert_called_once_with("token.txt")
        mock_teams_res_class.assert_called_once_with("token.txt")

        # Verify data was fetched
        mock_ideas_res.fetch_enhanced.assert_called_once()
        mock_teams_res.build_id_to_name_mapping.assert_called_once()

        # Verify data was processed
        mock_utils.process_ideas.assert_called_once()

        # Verify export was called
        mock_excel.export.assert_called_once()


class TestHandleTeamsCommand:
    """Test handle_teams_command() function"""

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_teams_basic(self, mock_teams_res_class, mock_excel):
        """Test basic teams command handling"""
        mock_teams_res = Mock()
        mock_teams_res_class.return_value = mock_teams_res

        mock_teams_res.fetch_list.return_value = {
            "results": [{"id": 1, "name": "Team 1"}]
        }

        args = Namespace(
            output='teams.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True
        )

        cli.handle_teams_command(args, "token.txt")

        # Verify resource was created
        mock_teams_res_class.assert_called_once_with("token.txt")

        # Verify data was fetched
        mock_teams_res.fetch_list.assert_called_once()

        # Verify export was called
        mock_excel.export.assert_called_once()


class TestHandleOKRsCommand:
    """Test handle_okrs_command() function"""

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.markdown')
    @patch('productplan_api_tools.cli.OKRsResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_okrs_excel_format(self, mock_teams_res_class, mock_okrs_res_class, mock_markdown, mock_excel):
        """Test OKRs command with Excel format"""
        mock_okrs_res = Mock()
        mock_teams_res = Mock()
        mock_okrs_res_class.return_value = mock_okrs_res
        mock_teams_res_class.return_value = mock_teams_res

        mock_teams_res.build_id_to_name_mapping.return_value = {10: "Engineering"}
        mock_okrs_res.fetch_enhanced.return_value = [{"objective_id": 1}]

        args = Namespace(
            output='okrs.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='excel'
        )

        cli.handle_okrs_command(args, "token.txt")

        # Should use Excel exporter
        mock_excel.export.assert_called_once()
        mock_markdown.export_okr.assert_not_called()

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.markdown')
    @patch('productplan_api_tools.cli.OKRsResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_okrs_markdown_format(self, mock_teams_res_class, mock_okrs_res_class, mock_markdown, mock_excel):
        """Test OKRs command with Markdown format"""
        mock_okrs_res = Mock()
        mock_teams_res = Mock()
        mock_okrs_res_class.return_value = mock_okrs_res
        mock_teams_res_class.return_value = mock_teams_res

        mock_teams_res.build_id_to_name_mapping.return_value = {}
        mock_okrs_res.fetch_enhanced.return_value = []

        args = Namespace(
            output='okrs.md',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='markdown'
        )

        cli.handle_okrs_command(args, "token.txt")

        # Should use Markdown exporter
        mock_markdown.export_okr.assert_called_once()
        mock_excel.export.assert_not_called()


class TestHandleObjectiveMapCommand:
    """Test handle_objectivemap_command() function"""

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.javascript')
    @patch('productplan_api_tools.cli.ObjectiveMappingResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_objectivemap_excel_format(self, mock_teams_res_class, mock_mapping_res_class, mock_js, mock_excel):
        """Test objectivemap command with Excel format"""
        mock_mapping_res = Mock()
        mock_teams_res = Mock()
        mock_mapping_res_class.return_value = mock_mapping_res
        mock_teams_res_class.return_value = mock_teams_res

        mock_teams_res.build_id_to_name_mapping.return_value = {}
        mock_mapping_res.fetch_mapping_data.return_value = []

        args = Namespace(
            output='mapping.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='excel'
        )

        cli.handle_objectivemap_command(args, "token.txt")

        # Should use Excel exporter
        mock_excel.export.assert_called_once()
        mock_js.export_miro.assert_not_called()

    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.javascript')
    @patch('productplan_api_tools.cli.ObjectiveMappingResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_objectivemap_javascript_format(self, mock_teams_res_class, mock_mapping_res_class, mock_js, mock_excel):
        """Test objectivemap command with JavaScript format"""
        mock_mapping_res = Mock()
        mock_teams_res = Mock()
        mock_mapping_res_class.return_value = mock_mapping_res
        mock_teams_res_class.return_value = mock_teams_res

        mock_teams_res.build_id_to_name_mapping.return_value = {}
        mock_mapping_res.fetch_mapping_data.return_value = []

        args = Namespace(
            output='objectives.js',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='javascript'
        )

        cli.handle_objectivemap_command(args, "token.txt")

        # Should use JavaScript exporter
        mock_js.export_miro.assert_called_once()
        mock_excel.export.assert_not_called()


class TestRouteCommand:
    """Test route_command() function"""

    @patch('os.path.isfile', return_value=True)
    @patch('productplan_api_tools.cli.handle_ideas_command')
    def test_route_command_ideas(self, mock_handler, mock_isfile):
        """Test routing to ideas handler"""
        args = Namespace(
            token_file='token.txt',
            endpoint='ideas'
        )

        cli.route_command(args)

        mock_handler.assert_called_once_with(args, 'token.txt')

    @patch('os.path.isfile', return_value=True)
    @patch('productplan_api_tools.cli.handle_teams_command')
    def test_route_command_teams(self, mock_handler, mock_isfile):
        """Test routing to teams handler"""
        args = Namespace(
            token_file='token.txt',
            endpoint='teams'
        )

        cli.route_command(args)

        mock_handler.assert_called_once_with(args, 'token.txt')

    @patch('os.path.isfile', return_value=False)
    def test_route_command_missing_token_file(self, mock_isfile):
        """Test that missing token file causes SystemExit"""
        args = Namespace(
            token_file='missing.txt',
            endpoint='ideas'
        )

        with pytest.raises(SystemExit):
            cli.route_command(args)

    @patch('os.path.isfile', return_value=True)
    def test_route_command_unknown_endpoint(self, mock_isfile):
        """Test that unknown endpoint raises error"""
        args = Namespace(
            token_file='token.txt',
            endpoint='unknown'
        )

        with pytest.raises((KeyError, SystemExit)):
            cli.route_command(args)
