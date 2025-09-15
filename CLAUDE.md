# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

### Build and Setup
```bash
# Build Docker image
make build

# Initial setup (creates token.txt and builds image)  
./setup.sh
```

### Data Fetching Commands
```bash
# Fetch ideas with detailed information (includes timestamps, custom dropdown fields, team columns, etc.)
make ideas

# Fetch teams data
make teams

# Fetch idea forms data with detailed information (includes custom fields, instructions, etc.)
make idea-forms

# Fetch objectives and key results (OKRs) data (active objectives by default, Excel format)
make okrs

# Fetch all objectives and key results (including inactive)
make okrs OBJECTIVE_STATUS=all OUTPUT=all_okrs.xlsx

# Generate OKRs in markdown format
make okrs OUTPUT_FORMAT=markdown OUTPUT=okrs.md

# Generate all OKRs in markdown format
make okrs OBJECTIVE_STATUS=all OUTPUT_FORMAT=markdown OUTPUT=all_okrs.md

# Fetch all data types (saves as ideas.xlsx, teams.xlsx, idea-forms.xlsx, and okrs.xlsx)
make all

# Custom endpoint with specific parameters
make custom ENDPOINT=idea-forms OUTPUT=custom.xlsx FILTERS="name:Feature Request"
make custom ENDPOINT=okrs OUTPUT=custom_okrs.xlsx FILTERS="name:Q4 Goals"
make custom ENDPOINT=okrs OUTPUT_FORMAT=markdown OUTPUT=quarterly_review.md OBJECTIVE_STATUS=all
```

### Common Parameters
- `OUTPUT=filename.xlsx` - Set output filename
- `FILTERS="key1:value1 key2:value2"` - Apply multiple filters
- `PAGE=num` - Set page number (default: 1)
- `PAGE_SIZE=num` - Set page size (default: 200, max: 500)
- `ALL_PAGES=true/false` - Fetch all pages (default: true)
- `LOCATION_STATUS=status` - Filter ideas by location status (default: not_archived)
  - Options: all, visible, hidden, archived, not_archived
- `OBJECTIVE_STATUS=status` - Filter objectives by status (default: active)
  - Options: active, all
- `OUTPUT_FORMAT=format` - Output format for OKRs (default: excel)
  - Options: excel, markdown

## Architecture Overview

This is a Python-based ProductPlan API client that runs in Docker containers with simplified Make commands.

### Core Components

1. **ProductPlanAPI class** (`productplan_api.py:13-176`)
   - Handles authentication via Bearer token from `token.txt`
   - Makes paginated requests to ProductPlan API v2
   - Supports ideas (`discovery/ideas`), teams, and idea forms (`discovery/idea_forms`) endpoints
   - Automatic pagination with `_fetch_all_pages` method

2. **DataExporter class** (`productplan_api.py:178-350`)
   - Exports data to Excel format using pandas
   - For ideas: processes custom text fields into separate columns with "Custom: " prefix
   - For ideas: adds team assignment columns (1 if assigned, 0 if not)
   - Handles JSON parsing of nested API response data

3. **Makefile-based interface** (`Makefile:1-119`)
   - Wraps Docker commands with simplified Make targets
   - Processes space-separated filter syntax (`key:value key2:value2`)
   - Handles parameter passing to Docker container

### Data Processing Flow

When fetching ideas:
1. API call retrieves paginated results from ProductPlan
2. For each idea, detailed information is fetched using individual idea endpoint
3. Location status filtering is applied (excludes archived ideas by default)
4. Team mapping is built from separate teams API call
5. Custom text fields are parsed and extracted into individual columns with "Custom: " prefix
6. Custom dropdown fields are parsed and extracted into individual columns with "Custom_Dropdown: " prefix
7. Team assignments are converted to binary columns (one per team)
8. Enhanced idea data with timestamps and all details is exported to Excel

When fetching idea forms:
1. API call retrieves list of idea forms from ProductPlan
2. For each form, detailed information is fetched using individual form endpoint
3. Custom text fields and dropdown fields are flattened into separate columns
4. Enhanced form data with all details is exported to Excel

### Key Files

- `productplan_api.py` - Main API client and data processing logic
- `Makefile` - Command interface with Docker integration
- `Dockerfile` - Python 3.9 container with pandas/requests dependencies
- `requirements.txt` - Python dependencies (requests, pandas, openpyxl, numpy)
- `token.txt` - ProductPlan API token (not in repo, created by setup.sh)

## OKR Usage Examples and Best Practices

### Basic OKR Commands

```bash
# Get active objectives only (default behavior)
make okrs

# Get all objectives including inactive ones
make okrs OBJECTIVE_STATUS=all

# Generate markdown report for quarterly review
make okrs OUTPUT_FORMAT=markdown OUTPUT=q1_okrs.md

# Get all objectives in markdown format with custom filename
make okrs OBJECTIVE_STATUS=all OUTPUT_FORMAT=markdown OUTPUT=company_okrs.md
```

### OKR Output Format Comparison

**Excel Format**: Best for data analysis, filtering, and integration with other tools
- Flattened tabular structure
- One row per key result (or objective if no key results)
- All data in columns for easy sorting/filtering
- Includes reference IDs for linking back to ProductPlan

**Markdown Format**: Best for documentation, reports, and team communication
- Hierarchical structure with clear headings
- Professional formatting for stakeholder reviews
- Easy to read and share
- Perfect for quarterly business reviews and team updates

### Integration Workflow Examples

```bash
# Weekly team review - get active OKRs in markdown
make okrs OUTPUT_FORMAT=markdown OUTPUT=weekly_review.md

# Quarterly analysis - get all OKRs in Excel for data analysis
make okrs OBJECTIVE_STATUS=all OUTPUT=quarterly_analysis.xlsx

# Executive summary - active OKRs in clean markdown format
make okrs OUTPUT_FORMAT=markdown OUTPUT=executive_summary.md

# Complete data export - all OKRs with full details in Excel
make okrs OBJECTIVE_STATUS=all OUTPUT=complete_okr_data.xlsx
```

### Understanding OKR Data Structure

**Team Resolution**: 
- Teams are automatically resolved from IDs to names
- Multiple teams per objective/key result are displayed as comma-separated values
- Team mapping is built once to avoid API rate limiting

**Key Result Names**: 
- Key result names come from the 'description' field in the ProductPlan API
- This ensures you get the actual key result descriptions, not generic identifiers

**Status Filtering**:
- `active` (default): Excludes archived, inactive, or deleted objectives
- `all`: Includes all objectives regardless of status for comprehensive reporting

**Progress Tracking**:
- Target: The goal value for the key result
- Current: The current progress value
- Progress: Progress percentage or completion metric

### API Endpoints Used

- `https://app.productplan.com/api/v2/discovery/ideas` - Ideas list
- `https://app.productplan.com/api/v2/discovery/ideas/{id}` - Individual idea details with timestamps and custom dropdown fields
- `https://app.productplan.com/api/v2/teams` - Team data for ID-to-name mapping
- `https://app.productplan.com/api/v2/discovery/idea_forms` - Idea form definitions
- `https://app.productplan.com/api/v2/discovery/idea_forms/{id}` - Individual idea form details
- `https://app.productplan.com/api/v2/strategy/objectives` - Objectives list
- `https://app.productplan.com/api/v2/strategy/objectives/{id}` - Individual objective details
- `https://app.productplan.com/api/v2/strategy/objectives/{objective_id}/key_results` - Key results for a specific objective

### Available Filters

**Ideas endpoint:**
- id, name, description, channel, customer, opportunities_count, source_name, source_email, location_status
- Enhanced processing fetches detailed information for each idea including:
  - Created and updated timestamps (created_at, updated_at)
  - Custom dropdown fields with values
  - Tags, opportunity_ids, idea_form_id
  - All fields are flattened for Excel export
- Default filtering excludes archived ideas (location_status != "archived")

**Teams endpoint:**  
- id, name

**Idea Forms endpoint:**
- Endpoint supports pagination and filtering (specific filters may vary)
- Enhanced processing fetches detailed information for each form including:
  - Form title, instructions, enabled status
  - Custom text fields with labels
  - Custom dropdown fields with labels and allowed values
  - Creation and update timestamps

**OKRs (Objectives and Key Results) endpoint:**
- **API Endpoints Used**: 
  - `https://app.productplan.com/api/v2/strategy/objectives` - Objectives list and details
  - `https://app.productplan.com/api/v2/strategy/objectives/{objective_id}/key_results` - Key results for each objective
- **Status Filtering**: By default, only active objectives are fetched (use OBJECTIVE_STATUS=all to get all objectives)
- **Output Formats**: Supports both Excel and Markdown export formats
- **Team Resolution**: Automatically resolves team IDs to team names using teams API mapping
- **Enhanced Processing**: Fetches detailed information for each objective and all associated key results
- **Excel Column Structure** (in order):
  - Status (location_status), team name, objective name, objective description
  - Key result name (from 'description' field), key result target, key result current, key result progress
  - Objective id, key result id (at the end for reference)
- **Markdown Structure**:
  - H1: "Objectives and Key Results" (document title)
  - H2: Objective name (clean, without team in parentheses)
  - Objective description (if available)
  - H3: "Team" section with team name
  - H3: "Key Results" section with bulleted list or "No key results"
  - Key result format: "- Description (target: value) - Current: X | Progress: Y"
- **Data Logic**:
  - If objective has key results: one row per key result (Excel) or bulleted list (Markdown)
  - If objective has no key results: one row with empty key result fields (Excel) or "No key results" (Markdown)
- **Team Mapping**: Checks key result team_id first, then objective team_id, supports multiple teams per objective