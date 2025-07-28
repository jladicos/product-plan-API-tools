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

# Fetch all data types (saves as ideas.xlsx, teams.xlsx, and idea-forms.xlsx)
make all

# Custom endpoint with specific parameters
make custom ENDPOINT=idea-forms OUTPUT=custom.xlsx FILTERS="name:Feature Request"
```

### Common Parameters
- `OUTPUT=filename.xlsx` - Set output filename
- `FILTERS="key1:value1 key2:value2"` - Apply multiple filters
- `PAGE=num` - Set page number (default: 1)
- `PAGE_SIZE=num` - Set page size (default: 200, max: 500)
- `ALL_PAGES=true/false` - Fetch all pages (default: true)
- `LOCATION_STATUS=status` - Filter ideas by location status (default: not_archived)
  - Options: all, visible, hidden, archived, not_archived

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

### API Endpoints Used

- `https://app.productplan.com/api/v2/discovery/ideas` - Ideas list
- `https://app.productplan.com/api/v2/discovery/ideas/{id}` - Individual idea details with timestamps and custom dropdown fields
- `https://app.productplan.com/api/v2/teams` - Team data for ID-to-name mapping
- `https://app.productplan.com/api/v2/discovery/idea_forms` - Idea form definitions
- `https://app.productplan.com/api/v2/discovery/idea_forms/{id}` - Individual idea form details

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