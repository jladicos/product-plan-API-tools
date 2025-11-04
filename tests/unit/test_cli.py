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
            assert args.page == 1
            assert args.page_size == 200
            assert args.output == 'files/productplan_data.xlsx'
            assert args.all_pages is False
            assert args.location_status == 'not_archived'
            assert args.objective_status == 'active'
            assert args.output_format == 'excel'
            assert args.output_type == 'auto'

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

    def test_parse_arguments_output_type_auto(self):
        """Test parsing --output-type auto"""
        with patch('sys.argv', ['script.py', '--output-type', 'auto']):
            args = cli.parse_arguments()
            assert args.output_type == 'auto'

    def test_parse_arguments_output_type_excel(self):
        """Test parsing --output-type excel"""
        with patch('sys.argv', ['script.py', '--output-type', 'excel']):
            args = cli.parse_arguments()
            assert args.output_type == 'excel'

    def test_parse_arguments_output_type_sheets(self):
        """Test parsing --output-type sheets"""
        with patch('sys.argv', ['script.py', '--output-type', 'sheets']):
            args = cli.parse_arguments()
            assert args.output_type == 'sheets'

    def test_parse_arguments_output_type_invalid(self):
        """Test that invalid --output-type raises error"""
        with patch('sys.argv', ['script.py', '--output-type', 'invalid']):
            with pytest.raises(SystemExit):
                cli.parse_arguments()


class TestHandleIdeasCommand:
    """Test handle_ideas_command() function"""

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.utils')
    @patch('productplan_api_tools.cli.IdeasResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_ideas_basic(self, mock_teams_res_class, mock_ideas_res_class, mock_utils, mock_excel, mock_get_token):
        """Test basic ideas command handling"""
        # Mock config
        mock_get_token.return_value = "test_token"

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

        cli.handle_ideas_command(args)

        # Verify token was fetched from config
        mock_get_token.assert_called_once()

        # Verify resources were created with token
        mock_ideas_res_class.assert_called_once_with("test_token")
        mock_teams_res_class.assert_called_once_with("test_token")

        # Verify data was fetched
        mock_ideas_res.fetch_enhanced.assert_called_once()
        mock_teams_res.build_id_to_name_mapping.assert_called_once()

        # Verify data was processed
        mock_utils.process_ideas.assert_called_once()

        # Verify export was called
        mock_excel.export.assert_called_once()

    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_handle_ideas_config_error(self, mock_get_token):
        """Test that config errors are raised properly"""
        mock_get_token.side_effect = ValueError("API token not configured")

        args = Namespace(
            output='output.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            location_status='not_archived'
        )

        with pytest.raises(ValueError, match="API token not configured"):
            cli.handle_ideas_command(args)


class TestHandleTeamsCommand:
    """Test handle_teams_command() function"""

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_teams_basic(self, mock_teams_res_class, mock_excel, mock_get_token):
        """Test basic teams command handling"""
        mock_get_token.return_value = "test_token"
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

        cli.handle_teams_command(args)

        # Verify resource was created
        mock_teams_res_class.assert_called_once_with("test_token")

        # Verify data was fetched
        mock_teams_res.fetch_list.assert_called_once()

        # Verify export was called
        mock_excel.export.assert_called_once()

    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_handle_teams_config_error(self, mock_get_token):
        """Test that config errors are raised properly"""
        mock_get_token.side_effect = ValueError("API token not configured")

        args = Namespace(
            output='teams.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True
        )

        with pytest.raises(ValueError, match="API token not configured"):
            cli.handle_teams_command(args)


class TestHandleOKRsCommand:
    """Test handle_okrs_command() function"""

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.markdown')
    @patch('productplan_api_tools.cli.OKRsResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_okrs_excel_format(self, mock_teams_res_class, mock_okrs_res_class, mock_markdown, mock_excel, mock_get_token):
        """Test OKRs command with Excel format"""
        mock_get_token.return_value = "test_token"
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

        cli.handle_okrs_command(args)

        # Should use Excel exporter
        mock_excel.export.assert_called_once()
        mock_markdown.export_okr.assert_not_called()

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.markdown')
    @patch('productplan_api_tools.cli.OKRsResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_okrs_markdown_format(self, mock_teams_res_class, mock_okrs_res_class, mock_markdown, mock_excel, mock_get_token):
        """Test OKRs command with Markdown format"""
        mock_get_token.return_value = "test_token"
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

        cli.handle_okrs_command(args)

        # Should use Markdown exporter
        mock_markdown.export_okr.assert_called_once()
        mock_excel.export.assert_not_called()

    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_handle_okrs_config_error(self, mock_get_token):
        """Test that config errors are raised properly"""
        mock_get_token.side_effect = ValueError("API token not configured")

        args = Namespace(
            output='okrs.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='excel'
        )

        with pytest.raises(ValueError, match="API token not configured"):
            cli.handle_okrs_command(args)


class TestHandleObjectiveMapCommand:
    """Test handle_objectivemap_command() function"""

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.javascript')
    @patch('productplan_api_tools.cli.ObjectiveMappingResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_objectivemap_excel_format(self, mock_teams_res_class, mock_mapping_res_class, mock_js, mock_excel, mock_get_token):
        """Test objectivemap command with Excel format"""
        mock_get_token.return_value = "test_token"
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

        cli.handle_objectivemap_command(args)

        # Should use Excel exporter
        mock_excel.export.assert_called_once()
        mock_js.export_miro.assert_not_called()

    @patch('productplan_api_tools.cli.config.get_api_token')
    @patch('productplan_api_tools.cli.exporters.excel')
    @patch('productplan_api_tools.cli.exporters.javascript')
    @patch('productplan_api_tools.cli.ObjectiveMappingResource')
    @patch('productplan_api_tools.cli.TeamsResource')
    def test_handle_objectivemap_javascript_format(self, mock_teams_res_class, mock_mapping_res_class, mock_js, mock_excel, mock_get_token):
        """Test objectivemap command with JavaScript format"""
        mock_get_token.return_value = "test_token"
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

        cli.handle_objectivemap_command(args)

        # Should use JavaScript exporter
        mock_js.export_miro.assert_called_once()
        mock_excel.export.assert_not_called()

    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_handle_objectivemap_config_error(self, mock_get_token):
        """Test that config errors are raised properly"""
        mock_get_token.side_effect = ValueError("API token not configured")

        args = Namespace(
            output='mapping.xlsx',
            page=1,
            page_size=200,
            filter=None,
            all_pages=True,
            objective_status='active',
            output_format='excel'
        )

        with pytest.raises(ValueError, match="API token not configured"):
            cli.handle_objectivemap_command(args)


class TestHandleSLAInitCommand:
    """Test handle_sla_init_command() function"""

    @patch('productplan_api_tools.cli.sla_init')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_basic(self, mock_get_token, mock_create_storage, mock_sla_init):
        """Test basic sla-init command handling"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='auto'
        )

        cli.handle_sla_init_command(args)

        # Verify token fetched
        mock_get_token.assert_called_once()

        # Verify storage created with output_path=None (let factory decide)
        mock_create_storage.assert_called_once_with(
            output_path=None,  # None lets factory auto-detect based on config
            output_type='auto'
        )

        # Verify sla_init called with storage and token
        mock_sla_init.assert_called_once_with(storage=mock_storage, token="test_token")

    @patch('productplan_api_tools.cli.sla_init')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_custom_output_path(self, mock_get_token, mock_create_storage, mock_sla_init):
        """Test sla-init with custom output path"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='custom/path.xlsx',
            output_type='auto'
        )

        cli.handle_sla_init_command(args)

        # Should use custom path, not default
        mock_create_storage.assert_called_once_with(
            output_path='custom/path.xlsx',
            output_type='auto'
        )

    @patch('productplan_api_tools.cli.sla_init')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_with_output_type_excel(self, mock_get_token, mock_create_storage, mock_sla_init):
        """Test sla-init with output_type=excel"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='excel'
        )

        cli.handle_sla_init_command(args)

        mock_create_storage.assert_called_once_with(
            output_path='files/sla_tracking.xlsx',
            output_type='excel'
        )

    @patch('productplan_api_tools.cli.sla_init')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_with_output_type_sheets(self, mock_get_token, mock_create_storage, mock_sla_init):
        """Test sla-init with output_type=sheets"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='sheets'
        )

        cli.handle_sla_init_command(args)

        mock_create_storage.assert_called_once_with(
            output_path=None,  # None lets factory use Google Sheets
            output_type='sheets'
        )

    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_config_error_propagates(self, mock_get_token, mock_create_storage):
        """Test that config errors propagate correctly"""
        mock_get_token.side_effect = ValueError("Config error: PRODUCTPLAN_API_TOKEN not set")

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='auto'
        )

        with pytest.raises(ValueError, match="Config error"):
            cli.handle_sla_init_command(args)

    @patch('productplan_api_tools.cli.sla_init')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_init_storage_error_propagates(self, mock_get_token, mock_create_storage, mock_sla_init):
        """Test that storage creation errors propagate correctly"""
        mock_get_token.return_value = "test_token"
        mock_create_storage.side_effect = ValueError("Google Sheets not configured")

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='sheets'
        )

        with pytest.raises(ValueError, match="Google Sheets not configured"):
            cli.handle_sla_init_command(args)


class TestHandleSLAUpdateCommand:
    """Test handle_sla_update_command() function"""

    @patch('productplan_api_tools.cli.sla_update')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_basic(self, mock_get_token, mock_create_storage, mock_sla_update):
        """Test basic sla-update command handling"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='auto'
        )

        cli.handle_sla_update_command(args)

        # Verify token fetched
        mock_get_token.assert_called_once()

        # Verify storage created with output_path=None (let factory decide)
        mock_create_storage.assert_called_once_with(
            output_path=None,  # None lets factory auto-detect based on config
            output_type='auto'
        )

        # Verify sla_update called with storage and token
        mock_sla_update.assert_called_once_with(storage=mock_storage, token="test_token")

    @patch('productplan_api_tools.cli.sla_update')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_custom_output_path(self, mock_get_token, mock_create_storage, mock_sla_update):
        """Test sla-update with custom output path"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='custom/path.xlsx',
            output_type='auto'
        )

        cli.handle_sla_update_command(args)

        # Should use custom path, not default
        mock_create_storage.assert_called_once_with(
            output_path='custom/path.xlsx',
            output_type='auto'
        )

    @patch('productplan_api_tools.cli.sla_update')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_with_output_type_excel(self, mock_get_token, mock_create_storage, mock_sla_update):
        """Test sla-update with output_type=excel"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='excel'
        )

        cli.handle_sla_update_command(args)

        mock_create_storage.assert_called_once_with(
            output_path='files/sla_tracking.xlsx',
            output_type='excel'
        )

    @patch('productplan_api_tools.cli.sla_update')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_with_output_type_sheets(self, mock_get_token, mock_create_storage, mock_sla_update):
        """Test sla-update with output_type=sheets"""
        mock_get_token.return_value = "test_token"
        mock_storage = Mock()
        mock_create_storage.return_value = mock_storage

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='sheets'
        )

        cli.handle_sla_update_command(args)

        mock_create_storage.assert_called_once_with(
            output_path=None,  # None lets factory use Google Sheets
            output_type='sheets'
        )

    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_config_error_propagates(self, mock_get_token, mock_create_storage):
        """Test that config errors propagate correctly"""
        mock_get_token.side_effect = ValueError("Config error: PRODUCTPLAN_API_TOKEN not set")

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='auto'
        )

        with pytest.raises(ValueError, match="Config error"):
            cli.handle_sla_update_command(args)

    @patch('productplan_api_tools.cli.sla_update')
    @patch('productplan_api_tools.cli.create_storage')
    @patch('productplan_api_tools.cli.config.get_api_token')
    def test_sla_update_storage_error_propagates(self, mock_get_token, mock_create_storage, mock_sla_update):
        """Test that storage creation errors propagate correctly"""
        mock_get_token.return_value = "test_token"
        mock_create_storage.side_effect = ValueError("Google Sheets not configured")

        args = Namespace(
            output='files/productplan_data.xlsx',
            output_type='sheets'
        )

        with pytest.raises(ValueError, match="Google Sheets not configured"):
            cli.handle_sla_update_command(args)


class TestRouteCommand:
    """Test route_command() function"""

    @patch('productplan_api_tools.cli.handle_ideas_command')
    def test_route_command_ideas(self, mock_handler):
        """Test routing to ideas handler"""
        args = Namespace(
            endpoint='ideas'
        )

        cli.route_command(args)

        mock_handler.assert_called_once_with(args)

    @patch('productplan_api_tools.cli.handle_teams_command')
    def test_route_command_teams(self, mock_handler):
        """Test routing to teams handler"""
        args = Namespace(
            endpoint='teams'
        )

        cli.route_command(args)

        mock_handler.assert_called_once_with(args)

    def test_route_command_unknown_endpoint(self):
        """Test that unknown endpoint raises SystemExit"""
        args = Namespace(
            endpoint='unknown'
        )

        with pytest.raises(SystemExit):
            cli.route_command(args)
