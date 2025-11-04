# ProductPlan API Client - User Guide

This guide will help you get started with the ProductPlan API Client using the new `make` commands.

## Getting Started

### First-Time Setup

1. Make sure you have Docker installed on your machine
2. Run the setup script:
   ```
   ./setup.sh
   ```
3. When prompted, enter your ProductPlan API token

### Troubleshooting Setup Script Issues

If you encounter issues running the setup script, try the following:

1. **"Command not found" error**:
   Make sure the script has executable permissions:
   ```bash
   chmod +x setup.sh
   ```
   Then try running it again:
   ```bash
   ./setup.sh
   ```

2. **Permission denied errors**:
   You may need to run the script with sudo:
   ```bash
   sudo ./setup.sh
   ```

3. **Line ending issues**:
   If the file was edited on Windows or transferred between systems:
   ```bash
   # Install dos2unix if needed:
   # Ubuntu/Debian: sudo apt-get install dos2unix
   # macOS: brew install dos2unix
   
   dos2unix setup.sh
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Manual script recreation**:
   If all else fails, you can recreate the script manually:
   ```bash
   # Create the script file with the correct contents
   cat > setup.sh << 'EOF'
   #!/bin/bash
   
   # ProductPlan API Client Setup Script
   # ... [script contents] ...
   EOF
   
   # Make it executable
   chmod +x setup.sh
   ```

### Quick Start Commands

| Command | Description |
|---------|-------------|
| `make ideas` | Get all ideas with team columns |
| `make teams` | Get all teams |
| `make idea-forms` | Get all idea forms with detailed information |
| `make okrs` | Get objectives and key results (OKRs) - Excel format |
| `make okrs output-format=markdown` | Get OKRs in Markdown format |
| `make all` | Get ideas, teams, idea forms, and OKRs |
| `make help` | See all available commands and options |

## Working with Ideas

### Basic Commands

```bash
# Get all ideas (saved to productplan_data.xlsx by default)
make ideas

# Specify a custom output filename
make ideas OUTPUT=my_ideas.xlsx

# Get ideas from a specific page only (not all pages)
make ideas ALL_PAGES=false PAGE=2
```

### Using Filters

You can filter the results using the `FILTERS` parameter with key:value format:

```bash
# Filter by name
make ideas FILTERS="name:Feature Request"

# Multiple filters (separate with spaces)
make ideas FILTERS="name:Feature Request channel:Sales"
```

## Working with Teams

The commands for teams are similar to those for ideas:

```bash
# Get all teams
make teams

# Specify a custom output filename
make teams OUTPUT=my_teams.xlsx

# Filter by team name
make teams FILTERS="name:Product Team"
```

## Working with Idea Forms

The commands for idea forms follow the same pattern, but with enhanced functionality:

```bash
# Get all idea forms with detailed information (includes custom fields, instructions, etc.)
make idea-forms

# Specify a custom output filename
make idea-forms OUTPUT=my_forms.xlsx

# Filter idea forms (filters may vary based on your ProductPlan configuration)
make idea-forms FILTERS="name:Feature Form"
```

### Enhanced Idea Forms Data

When fetching idea forms, the tool automatically:
- Retrieves detailed information for each form using individual API calls
- Flattens custom text fields into separate columns (e.g., `Custom_Text_Field_1_Label`)
- Flattens custom dropdown fields with their allowed values (e.g., `Custom_Dropdown_Field_1_Allowed_Values`)
- Includes form metadata like title, instructions, enabled status, and timestamps

This provides much richer data than the basic form list endpoint.

## Working with OKRs (Objectives and Key Results)

The OKR endpoint provides comprehensive data about your organization's objectives and key results with enhanced functionality:

```bash
# Get all active objectives and key results (Excel format)
make okrs

# Get all objectives (including inactive) in Excel format
make okrs OBJECTIVE_STATUS=all

# Get active OKRs in Markdown format for documentation
make okrs output-format=markdown

# Specify a custom output filename
make okrs OUTPUT=quarterly_okrs.xlsx

# Custom filename for markdown format
make okrs output-format=markdown OUTPUT=team_okrs.md

# Get all objectives (active and inactive) in markdown format
make okrs output-format=markdown OBJECTIVE_STATUS=all OUTPUT=all_okrs.md
```

### OKR Data Structure

The OKR endpoint automatically:
- Fetches all objectives from your ProductPlan account
- Retrieves detailed key results for each objective
- Resolves team IDs to team names for both objectives and key results
- Filters to active objectives by default (use `OBJECTIVE_STATUS=all` to include inactive)
- Exports in Excel or Markdown format depending on your preference

### Excel Format Features

When using Excel format (default), the tool provides:
- **Flattened Structure**: One row per key result, or one row per objective if no key results
- **Column Order**: status, team_name, objective_name, objective_description, key_result_name, key_result_target, key_result_current, key_result_progress, objective_id, key_result_id
- **Team Resolution**: Automatic conversion of team IDs to readable team names
- **Progress Tracking**: Clear visibility of current values vs targets

### Markdown Format Features

When using `output-format=markdown`, the tool generates a structured document perfect for:
- **Team Reports**: Quarterly and annual objective reviews
- **Stakeholder Updates**: Executive summaries and board presentations
- **Documentation**: Knowledge base and planning documents

#### Markdown Structure Example

```markdown
# Objectives and Key Results

## Improve Customer Satisfaction
Enhance overall customer experience and reduce support tickets.

### Team
Customer Success Team

### Key Results
- Reduce average response time (target: 2 hours) - Current: 3.5 hours | Progress: 45%
- Increase NPS score (target: 50) - Current: 42 | Progress: 84%
- Implement self-service portal (target: 100%) - Current: 75% | Progress: 75%

## Launch New Product Feature

### Team
Product Development Team

### Key Results
No key results
```

### OKR Filtering Options

```bash
# Status filtering
make okrs OBJECTIVE_STATUS=active    # Default: only active objectives
make okrs OBJECTIVE_STATUS=all       # Include inactive objectives

# Output format options
make okrs output-format=excel        # Default: Excel spreadsheet
make okrs output-format=markdown     # Structured markdown document
```

## Advanced Usage

### Custom Commands

For maximum flexibility, use the `custom` command:

```bash
make custom ENDPOINT=idea-forms OUTPUT=custom.xlsx PAGE_SIZE=500

# Custom OKR export with specific settings
make custom ENDPOINT=okrs OUTPUT_FORMAT=markdown OUTPUT=quarterly_okrs.md OBJECTIVE_STATUS=all
```

### All Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `OUTPUT` | Output filename | productplan_data.xlsx |
| `PAGE` | Page number | 1 |
| `PAGE_SIZE` | Number of items per page | 200 |
| `ALL_PAGES` | Fetch all pages | true |
| `LOCATION_STATUS` | Filter ideas by location status | not_archived |
| `OBJECTIVE_STATUS` | Filter objectives by status | active |
| `OUTPUT_FORMAT` | Output format for OKRs | excel |
| `OUTPUT_TYPE` | SLA storage type | auto |
| `FILTERS` | Space-separated key:value pairs | (none) |

**Note:** API token is configured in `env/.env` file (PRODUCTPLAN_API_TOKEN variable)

## Using Direct Docker Commands

You can still use the direct Docker commands if needed:

```bash
# Ideas endpoint
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --all-pages --output output.xlsx

# Teams endpoint
docker run --rm -v $(pwd):/app productplan-api --endpoint teams --all-pages --output output.xlsx

# Idea forms endpoint with detailed information
docker run --rm -v $(pwd):/app productplan-api --endpoint idea-forms --all-pages --output output.xlsx

# OKRs endpoint (Excel format)
docker run --rm -v $(pwd):/app productplan-api --endpoint okrs --all-pages --output okrs.xlsx

# OKRs endpoint (Markdown format)
docker run --rm -v $(pwd):/app productplan-api --endpoint okrs --all-pages --output-format markdown --output okrs.md

# OKRs with all objectives (including inactive)
docker run --rm -v $(pwd):/app productplan-api --endpoint okrs --all-pages --objective-status all --output all_okrs.xlsx
```

## Troubleshooting

### Common Issues

1. **Configuration File Missing**:
   - Error: "Configuration file not found: env/.env"
   - Solution: Copy `env/.env.sample` to `env/.env` and add your API token
   - Command: `cp env/.env.sample env/.env`

2. **Authentication Failed (401)**:
   - Verify that `PRODUCTPLAN_API_TOKEN` in `env/.env` is correct and not expired
   - Ensure there are no extra spaces or quotes around the token value
   - Check that the env/.env file is in the correct location

3. **Permission Error When Writing Output**:
   - Make sure you're running the command in a directory where you have write permissions
   - Try specifying a different output path: `make ideas OUTPUT=/path/to/output.xlsx`

4. **Docker Not Running**:
   - Make sure Docker Desktop is running on your machine
   - Try restarting Docker if you're having issues

5. **"make: command not found" Error**:
   - Install Make:
	 - On macOS: `brew install make`
	 - On Ubuntu/Debian: `sudo apt-get install make`
	 - On Fedora/RHEL: `sudo dnf install make`

5. **Docker Image Issues**:
   - If you're having problems with the Docker image, try rebuilding it:
	 ```bash
	 make build
	 ```
   - Check your Docker installation with: `docker info`

### Getting Help

For more information:
- Run `make help` to see all available commands and options
- Refer to the README.md file for detailed documentation
- Check the ProductPlan API documentation for endpoint details