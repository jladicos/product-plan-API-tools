"""
Integration tests for Makefile

Tests that Makefile targets generate correct Docker commands with proper
variable substitution, defaults, and argument passing.

Uses `make -n` (dry-run) to inspect commands without executing them.
"""

import subprocess
import pytest


class TestMakefileVariables:
    """Test Makefile variable declarations and defaults"""

    def test_output_type_default_is_auto(self):
        """Test that OUTPUT_TYPE defaults to 'auto'"""
        result = subprocess.run(
            ['make', '-n', 'sla-init'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type auto' in result.stdout, \
            "OUTPUT_TYPE should default to 'auto'"

    def test_output_type_can_be_overridden(self):
        """Test that OUTPUT_TYPE can be set via command line"""
        result = subprocess.run(
            ['make', '-n', 'sla-init', 'OUTPUT_TYPE=excel'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type excel' in result.stdout, \
            "OUTPUT_TYPE=excel should pass --output-type excel"

    def test_output_type_lowercase_alias(self):
        """Test that lowercase output_type works"""
        result = subprocess.run(
            ['make', '-n', 'sla-init', 'output_type=sheets'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type sheets' in result.stdout, \
            "output_type=sheets should pass --output-type sheets"

    def test_output_type_hyphenated_lowercase_alias(self):
        """Test that lowercase output-type works"""
        result = subprocess.run(
            ['make', '-n', 'sla-init', 'output-type=excel'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type excel' in result.stdout, \
            "output-type=excel should pass --output-type excel"


class TestMakefileTokenFileRemoval:
    """Test that --token-file has been removed from all commands"""

    def test_ideas_no_token_file(self):
        """Test that 'make ideas' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'ideas'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "ideas command should not contain --token-file"

    def test_teams_no_token_file(self):
        """Test that 'make teams' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'teams'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "teams command should not contain --token-file"

    def test_idea_forms_no_token_file(self):
        """Test that 'make idea-forms' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'idea-forms'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "idea-forms command should not contain --token-file"

    def test_okrs_no_token_file(self):
        """Test that 'make okrs' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'okrs'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "okrs command should not contain --token-file"

    def test_objectivemap_no_token_file(self):
        """Test that 'make objectivemap' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'objectivemap'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "objectivemap command should not contain --token-file"

    def test_sla_init_no_token_file(self):
        """Test that 'make sla-init' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'sla-init'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "sla-init command should not contain --token-file"

    def test_sla_update_no_token_file(self):
        """Test that 'make sla-update' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'sla-update'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "sla-update command should not contain --token-file"

    def test_custom_no_token_file(self):
        """Test that 'make custom' does not pass --token-file"""
        result = subprocess.run(
            ['make', '-n', 'custom', 'ENDPOINT=ideas'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--token-file' not in result.stdout, \
            "custom command should not contain --token-file"


class TestMakefileOutputTypeScope:
    """Test that --output-type only appears in SLA commands"""

    def test_ideas_no_output_type(self):
        """Test that 'make ideas' does not pass --output-type"""
        result = subprocess.run(
            ['make', '-n', 'ideas'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type' not in result.stdout, \
            "ideas command should not contain --output-type (uses --output-format)"

    def test_teams_no_output_type(self):
        """Test that 'make teams' does not pass --output-type"""
        result = subprocess.run(
            ['make', '-n', 'teams'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type' not in result.stdout, \
            "teams command should not contain --output-type"

    def test_okrs_no_output_type(self):
        """Test that 'make okrs' does not pass --output-type"""
        result = subprocess.run(
            ['make', '-n', 'okrs'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type' not in result.stdout, \
            "okrs command should not contain --output-type (uses --output-format)"

    def test_sla_init_has_output_type(self):
        """Test that 'make sla-init' passes --output-type"""
        result = subprocess.run(
            ['make', '-n', 'sla-init'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type' in result.stdout, \
            "sla-init command should contain --output-type"

    def test_sla_update_has_output_type(self):
        """Test that 'make sla-update' passes --output-type"""
        result = subprocess.run(
            ['make', '-n', 'sla-update'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-type' in result.stdout, \
            "sla-update command should contain --output-type"


class TestMakefileSLACommands:
    """Test SLA-specific Makefile behavior"""

    def test_sla_init_default_output_path(self):
        """Test that sla-init uses files/sla_tracking.xlsx as default"""
        result = subprocess.run(
            ['make', '-n', 'sla-init'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output files/sla_tracking.xlsx' in result.stdout, \
            "sla-init should default to files/sla_tracking.xlsx"

    def test_sla_init_custom_output_path(self):
        """Test that sla-init respects custom OUTPUT"""
        result = subprocess.run(
            ['make', '-n', 'sla-init', 'OUTPUT=custom/path.xlsx'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output custom/path.xlsx' in result.stdout, \
            "sla-init should respect OUTPUT=custom/path.xlsx"

    def test_sla_update_default_output_path(self):
        """Test that sla-update uses files/sla_tracking.xlsx as default"""
        result = subprocess.run(
            ['make', '-n', 'sla-update'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output files/sla_tracking.xlsx' in result.stdout, \
            "sla-update should default to files/sla_tracking.xlsx"

    def test_sla_init_with_all_options(self):
        """Test that sla-init passes both output and output-type"""
        result = subprocess.run(
            ['make', '-n', 'sla-init', 'OUTPUT=test.xlsx', 'OUTPUT_TYPE=excel'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output test.xlsx' in result.stdout, \
            "sla-init should pass custom output"
        assert '--output-type excel' in result.stdout, \
            "sla-init should pass custom output-type"


class TestMakefileDockerCommand:
    """Test that Docker commands are properly formed"""

    def test_ideas_basic_command_structure(self):
        """Test that ideas command has correct Docker structure"""
        result = subprocess.run(
            ['make', '-n', 'ideas'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        # Should have docker run with volume mount and productplan-api image
        assert 'docker run' in result.stdout
        assert '--rm' in result.stdout
        assert 'productplan-api' in result.stdout
        assert '--endpoint ideas' in result.stdout

    def test_sla_init_basic_command_structure(self):
        """Test that sla-init command has correct Docker structure"""
        result = subprocess.run(
            ['make', '-n', 'sla-init'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        # Should have docker run with volume mount and productplan-api image
        assert 'docker run' in result.stdout
        assert '--rm' in result.stdout
        assert 'productplan-api' in result.stdout
        assert '--endpoint sla-init' in result.stdout
        assert '--output files/sla_tracking.xlsx' in result.stdout
        assert '--output-type auto' in result.stdout


class TestMakefileOtherVariables:
    """Test that other variables still work correctly"""

    def test_output_variable_override(self):
        """Test that OUTPUT variable can be overridden"""
        result = subprocess.run(
            ['make', '-n', 'ideas', 'OUTPUT=custom.xlsx'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output custom.xlsx' in result.stdout

    def test_output_lowercase_alias(self):
        """Test that lowercase output variable works"""
        result = subprocess.run(
            ['make', '-n', 'ideas', 'output=lowercase.xlsx'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output lowercase.xlsx' in result.stdout

    def test_location_status_variable(self):
        """Test that LOCATION_STATUS variable works"""
        result = subprocess.run(
            ['make', '-n', 'ideas', 'LOCATION_STATUS=all'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--location-status all' in result.stdout

    def test_objective_status_variable(self):
        """Test that OBJECTIVE_STATUS variable works"""
        result = subprocess.run(
            ['make', '-n', 'okrs', 'OBJECTIVE_STATUS=all'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--objective-status all' in result.stdout

    def test_output_format_variable(self):
        """Test that OUTPUT_FORMAT variable works"""
        result = subprocess.run(
            ['make', '-n', 'okrs', 'OUTPUT_FORMAT=markdown'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        assert '--output-format markdown' in result.stdout
