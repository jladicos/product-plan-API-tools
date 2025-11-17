# ProductPlan API Client

A flexible Python script to fetch data from the ProductPlan API and export it to Excel format, designed to run in a Docker container with simplified `make` commands.

## Features

- Fetch ideas from ProductPlan API
- Fetch teams from ProductPlan API
- Fetch idea forms from ProductPlan API with detailed information (includes custom fields, instructions, etc.)
- Fetch objectives and key results (OKRs) from ProductPlan API
- SLA tracking for customer ideas - Monitor response and roadmap decision timelines
  - Excel or Google Sheets output
  - Automatic URL generation for direct links to ideas
  - Smart team column ordering (sorted by ID, positioned last for stability)
- Export data to Excel format
- Export OKR data to Markdown format for documentation and reporting
- Filter results using command-line arguments
- Filter objectives by status (active/all)
- Pagination support
- Environment-based configuration (env/.env)
- Automatic team columns on ideas exports (1 if assigned, 0 if not)
- Automatic team name resolution for objectives and key results
- Automatic extraction of custom text fields into separate columns
- Simplified `make` commands for ease of use
- Docker containerization for easy deployment
- Organized file output - All generated files saved to `files/` directory by default

## File Organization

All generated files are automatically saved to the `files/` directory:
- `files/ideas.xlsx` - Ideas data with custom fields and team assignments
- `files/teams.xlsx` - Team information
- `files/idea-forms.xlsx` - Idea form definitions
- `files/okrs.xlsx` or `files/okrs.md` - Objectives and key results data
- `files/sla_tracking.xlsx` - SLA tracking spreadsheet for monitoring response and roadmap timelines
- The `files/` directory is git-ignored to keep your repository clean
- The script automatically creates this directory if it doesn't exist

## Setup

### Prerequisites

- Docker installed on your system
- Make installed on your system (pre-installed on macOS and Linux)
- A valid ProductPlan API token

### Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/jladicos/product-plan-API-tools
   cd productplan-api-client
   ```

2. Configure your environment:
   ```bash
   # Copy the sample environment file
   cp env/.env.sample env/.env

   # Edit env/.env and add your ProductPlan API token
   # Required: PRODUCTPLAN_API_TOKEN
   # Required: PRODUCTPLAN_URL_PREFIX
   # Optional: Google Sheets credentials (see Google Sheets Setup below)
   ```

3. Run the setup script to build the Docker image:
   ```bash
   ./setup.sh
   ```

   The setup script will:
   - Check for Docker and Make installation
   - Help you create env/.env file if it doesn't exist
   - Build the Docker image
   - Provide quick-start instructions

### Google Sheets Setup (Optional)

If you want to use Google Sheets instead of Excel for SLA tracking, you'll need Google Cloud credentials:

1. **Create a Google Cloud Project:**
   - Go to https://console.cloud.google.com/
   - Create a new project (or use an existing one)

2. **Enable Google Sheets API:**
   - In your project, go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

3. **Create a Service Account:**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "+ CREATE SERVICE ACCOUNT"
   - Name it (e.g., "productplan-sla-tracking")
   - Click "Create and Continue" (skip optional steps)

4. **Create and Download Key:**
   - Click on your new service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Click "Create" - this downloads a JSON file

5. **Save the Credentials:**
   - Copy the downloaded JSON file to: `env/google-credentials.json`
   - The `env/` folder is git-ignored for security
   - See `env/google-credentials-sample.json` for the expected format

6. **Share Your Google Sheet:**
   - Open the `client_email` from your JSON file (e.g., `your-service-account@your-project.iam.gserviceaccount.com`)
   - Share your Google Sheet with this email address
   - Give it "Editor" permissions

## Testing

This project includes a comprehensive test suite with 321 total tests ensuring reliability and preventing regressions.

### Test Types

**Unit Tests** - Test individual components in isolation (283 tests):
- Test all package components (resources, exporters, utils, CLI, SLA tracking, config)
- Mock external dependencies (HTTP requests, file I/O)
- Fast execution (~1 second)
- 100% coverage of architecture
- Run automatically on every change
- Run with: `make test`

**Integration Tests** - Test end-to-end workflows and command generation (28 tests):
- Makefile command generation with proper variable substitution
- SLA tracking workflows (init, update, URL generation, team ordering)
- Test actual Docker commands without executing them
- Verify system integration points
- Run with: `make test`

**Smoke Tests (Real API)** - Verify API contracts haven't changed (10 tests):
- Hit actual ProductPlan API endpoints
- Test authentication, teams, ideas, OKRs, idea forms, objective mapping
- Require valid env/.env file with PRODUCTPLAN_API_TOKEN
- Run occasionally (before releases, after API changes)
- Skip gracefully if env/.env is missing
- Run with: `make test-smoke`

### Running Tests

```bash
# Run unit and integration tests (recommended for development)
make test

# Run smoke tests against real API (requires env/.env with API token)
make test-smoke

# Run all tests (unit + integration + smoke)
make test-all
```

### Test Results Summary

- **Unit Tests**: 283/283 passing (100%)
- **Integration Tests**: 28/28 passing (100%)
- **Smoke Tests**: 10/10 passing (100%)
- **Total Tests**: 321/321 passing (100%)
- **All Tests Verified**: ✅ November 4, 2025

### Test Coverage

The test suite provides comprehensive coverage:
- ✅ All API endpoints (ideas, teams, OKRs, idea forms)
- ✅ SLA tracking (calculator, storage, manager, integration)
- ✅ Pagination (multi-page, single page, empty results)
- ✅ Filtering (basic filters, location_status, objective_status)
- ✅ Custom field parsing and extraction
- ✅ Team mapping and binary columns
- ✅ Excel, Markdown, and JavaScript exports
- ✅ Error handling and edge cases

### When to Run Tests

- **Integration tests**: Run frequently during development (fast, no API calls)
- **Smoke tests**: Run before releases or when API changes are suspected
- **All tests**: Run before major releases or refactoring

For more details, see `tests/smoke/README.md`.

## Usage with Make Commands

### Basic Usage

Use these simplified commands to get data from the ProductPlan API:

```bash
# Fetch all ideas (with team columns)
make ideas

# Fetch all teams
make teams

# Fetch all idea forms with detailed information
make idea-forms

# Fetch objectives and key results (OKRs) - Excel format
make okrs

# Fetch objectives and key results (OKRs) - Markdown format
make okrs output-format=markdown

# Fetch all data types (saved as ideas.xlsx, teams.xlsx, idea-forms.xlsx, and okrs.xlsx)
make all

# See all available commands and options
make help
```

### SLA Tracking

Track service level agreement (SLA) compliance for customer ideas with automated monitoring of response and roadmap decision timelines.

#### SLA Metrics

The SLA tracking system monitors two key metrics:

1. **Response SLA (14 days)**: Idea status must change from "On deck" to any other status within 14 days of creation
2. **Roadmap SLA (60 days)**: Idea must reach a final decision ("Accepted" or "Rejected") within 60 days of creation

#### SLA Commands

```bash
# Initialize SLA tracking spreadsheet (first-time setup)
# Auto-detects output: Google Sheets if configured, Excel otherwise
make sla-init

# Update SLA tracking spreadsheet (daily updates)
make sla-update

# Force Excel output (even if Google Sheets is configured)
make sla-init OUTPUT_TYPE=excel
make sla-update OUTPUT_TYPE=excel

# Force Google Sheets output (requires Google Sheets configuration)
make sla-init OUTPUT_TYPE=sheets
make sla-update OUTPUT_TYPE=sheets

# Custom output filename (implies Excel format)
make sla-init OUTPUT=files/custom_sla.xlsx
make sla-update OUTPUT=files/custom_sla.xlsx
```

#### How SLA Tracking Works

**Initialization** (`make sla-init`):
- Fetches all ideas from ProductPlan (including archived, but excluding "Ignore" status)
- Applies filtering rules to exclude test/development ideas
- Calculates SLA dates based on current idea status
- Creates Excel spreadsheet with full audit trail

**Daily Updates** (`make sla-update`):
- Fetches ideas updated in the last 14 days (buffer for missed runs, excluding "Ignore" status)
- Compares with existing spreadsheet
- Updates changed ideas (preserves historical SLA dates)
- Adds new ideas that pass filtering
- Removes ideas that now fail filtering (including ideas changed to "Ignore" status)

**SLA Date Logic**:
- **response_sla**: Set once when status changes from "On deck" (never cleared)
- **roadmap_sla**: Set once when status becomes "Accepted" or "Rejected" (never cleared)
- **Historical preservation**: SLA dates are audit trail - once set, never modified
- **Current compliance**: Boolean columns reflect whether idea currently meets criteria

#### Spreadsheet Column Structure

The SLA tracking spreadsheet includes columns in this specific order:

**Core Columns:**
- `id`: Idea ID (used as unique identifier)
- `url`: Direct link to the idea in ProductPlan (auto-generated from PRODUCTPLAN_URL_PREFIX + id)
- `name`, `description`, `customer`, `source_name`, `source_email`: Core idea information

**Timestamps:**
- `created_at`: When idea was created in ProductPlan
- `updated_at`: When idea was last modified

**SLA Tracking:**
- `response_sla`: Date when status first changed from "On deck" (historical, never cleared)
- `roadmap_sla`: Date when status became "Accepted" or "Rejected" (historical, never cleared)
- `response_sla_in_good_standing`: Boolean - is idea in good standing for response? (met SLA OR still within 14-day window)
- `roadmap_sla_in_good_standing`: Boolean - is idea in good standing for roadmap? (met SLA OR still within 60-day window)
- `currently_meets_response_sla`: Boolean - does idea currently meet 14-day response SLA?
- `currently_meets_roadmap_sla`: Boolean - does idea currently meet 60-day roadmap SLA?

**Status:**
- `idea_status`: Current status from custom dropdown ("On deck", "In Review", "Accepted", "Rejected")
- `location_status`: Visibility status (visible, hidden, archived)

**Custom Fields:**
- Additional custom text and dropdown fields from ProductPlan (dynamic, varies by instance)

**Team Assignments (Always Last):**
- Binary columns (1/0) for each team indicating assignment
- **Important**: Team columns are always positioned LAST (after all other columns including custom fields)
- Sorted by team ID numerically (e.g., "Team_1", "Team_2", "Team_100")
- This ensures new teams or custom fields don't shift existing column positions

#### Understanding "In Good Standing" Columns

The `response_sla_in_good_standing` and `roadmap_sla_in_good_standing` columns help distinguish between ideas that have **missed their deadline** versus ideas that are **still within the allowed window**.

**Response SLA In Good Standing** (TRUE when):
- Idea responded within 14 days (status changed from "On deck" on time), OR
- Idea is still within the 14-day window and hasn't been responded to yet

**Roadmap SLA In Good Standing** (FALSE when):
- Idea missed the 14-day response deadline

**Roadmap SLA In Good Standing** (TRUE when):
- Idea reached decision within 60 days (status became "Accepted" or "Rejected" on time), OR
- Idea is still within the 60-day window and hasn't reached a decision yet

**Roadmap SLA In Good Standing** (FALSE when):
- Idea missed the 60-day roadmap deadline

#### Calculating SLA Compliance Percentages

Use the "in good standing" columns to calculate accurate compliance percentages:

**Response SLA Compliance %:**
```
= COUNT(response_sla_in_good_standing = TRUE) / TOTAL_IDEAS
```

**Roadmap SLA Compliance %:**
```
= COUNT(roadmap_sla_in_good_standing = TRUE) / TOTAL_IDEAS
```

**Example Google Sheets formulas:**
```
# Response SLA compliance (assuming data in rows 2-100)
=COUNTIF(M2:M100, TRUE) / COUNTA(A2:A100)

# Roadmap SLA compliance
=COUNTIF(N2:N100, TRUE) / COUNTA(A2:A100)

# Team-specific compliance (assuming "Engineering" in column W)
=COUNTIFS(M2:M100, TRUE, W2:W100, 1) / COUNTIF(W2:W100, 1)
```

Replace column letters (M, N, W) with your actual column positions. Adjust row ranges (2:100) to match your data.

#### Run Tracking and Audit Trail

The SLA tracking system automatically maintains an audit trail of all executions in a separate "Runs" sheet/tab within your SLA tracking workbook.

**Automatic Tracking:**
- Every `make sla-init` and `make sla-update` execution is automatically recorded
- Tracking occurs only for successful runs (failures are not recorded)
- Runs sheet is auto-created on first execution if it doesn't exist
- Works with both Excel and Google Sheets output formats

**Runs Sheet Structure:**
- `type`: Type of execution ("init" or "update")
- `timestamp`: Execution timestamp in UTC timezone (format: YYYY-MM-DD HH:MM:SS)
- `records_added`: Number of ideas added during this run
- `records_updated`: Number of ideas updated during this run

**UTC Timezone:**
- **All timestamps use UTC timezone** for consistency across timezones
- This includes timestamps in the main SLA tracking sheet (`created_at`, `updated_at`, `response_sla`, `roadmap_sla`)
- UTC ensures reliable time tracking regardless of server location or daylight saving time

**Configuration:**
- The Runs sheet name defaults to "Runs" but can be customized via `GOOGLE_SHEET_RUNS_NAME` in `env/.env`
- Example: `GOOGLE_SHEET_RUNS_NAME=Audit Log` to use "Audit Log" instead of "Runs"

**Use Cases:**
- Monitor execution frequency and timing
- Verify data freshness (when was the last update?)
- Track data growth over time (records added/updated trends)
- Debug issues by reviewing execution history

#### Filtering Rules

To exclude test and development ideas, the following filters are applied:

1. **Date cutoff**: Ideas created before September 15, 2025 are excluded
2. **Jason Ladicos filter**: Ideas from "Jason Ladicos" created before November 3, 2025 are excluded (test data)
3. **TEST customer filter**: Ideas with customer="TEST" (exact match) are excluded

These filters are case-sensitive and require exact matches.

#### Usage Example

```bash
# Initial setup (first time)
make sla-init

# Expected output:
# - Fetches all ideas from ProductPlan
# - Applies filtering rules
# - Creates files/sla_tracking.xlsx
# - Shows SLA compliance summary

# Daily updates (run via cron or Apple Shortcut)
make sla-update

# Expected output:
# - Fetches recently updated ideas (last 14 days)
# - Updates changed ideas (preserves historical SLA dates)
# - Shows changes summary (Added: X, Updated: Y, Removed: Z)
# - Shows current SLA compliance statistics
```

#### Best Practices

- **Run `sla-init` once** to create the initial spreadsheet
- **Run `sla-update` daily** to keep tracking current (via cron job or Apple Shortcut)
- **14-day lookback buffer** ensures missed runs don't lose updates
- **Historical SLA dates preserved** - provides audit trail of when criteria were first met
- **Current compliance tracked** - boolean columns update if status regresses

### Customizing Output Filename

All files are saved to the `files/` directory by default. You can specify custom filenames:

```bash
# Set custom output filename (still goes to files/ directory by default)
make ideas OUTPUT=files/my_ideas.xlsx
make teams OUTPUT=files/my_teams.xlsx
make idea-forms OUTPUT=files/my_forms.xlsx
make okrs OUTPUT=files/my_okrs.xlsx

# Custom filename for markdown format
make okrs output-format=markdown output=files/my_okrs.md

# Or use a different directory if needed
make ideas OUTPUT=custom_dir/ideas.xlsx
```

### Filtering Results

Use the FILTERS parameter with key:value pairs (separate multiple filters with spaces):

```bash
# Single filter
make ideas FILTERS="name:Feature Request"

# Multiple filters
make ideas FILTERS="name:Feature Request channel:Sales"

# Filter ideas by location status
make ideas LOCATION_STATUS=all          # Include all ideas (visible, hidden, archived)
make ideas LOCATION_STATUS=not_archived # Exclude archived ideas (default)
make ideas LOCATION_STATUS=visible      # Only visible ideas

# Filter ideas by idea status (exclude/include "Ignore" status)
make ideas                              # Excludes ideas with "Ignore" status (default)
make ideas IDEA_STATUS=all              # Includes ideas with "Ignore" status

# Filter objectives by status
make okrs OBJECTIVE_STATUS=all          # Include inactive objectives
make okrs OBJECTIVE_STATUS=active       # Active objectives only (default)
```

### Pagination Options

```bash
# Get only a specific page (not all pages)
make ideas ALL_PAGES=false PAGE=2

# Customize page size
make ideas PAGE_SIZE=500
```

### Advanced Usage

For maximum flexibility, use the `custom` command:

```bash
make custom ENDPOINT=idea-forms OUTPUT=custom.xlsx PAGE_SIZE=500 FILTERS="name:New Feature"

# Custom OKR export with markdown format
make custom ENDPOINT=okrs OUTPUT_FORMAT=markdown OUTPUT=quarterly_okrs.md OBJECTIVE_STATUS=all
```

## Usage with Direct Docker Commands

You can still use the direct Docker commands if needed. Remember to include the `files/` directory in output paths:

```bash
# Fetch the first page of ideas (includes team columns)
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --output files/ideas.xlsx

# Fetch all ideas
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --all-pages --output files/ideas.xlsx

# Fetch all teams
docker run --rm -v $(pwd):/app productplan-api --endpoint teams --all-pages --output files/teams.xlsx

# Fetch all idea forms with detailed information
docker run --rm -v $(pwd):/app productplan-api --endpoint idea-forms --all-pages --output files/idea-forms.xlsx

# Fetch all active objectives and key results (Excel format)
docker run --rm -v $(pwd):/app productplan-api --endpoint okrs --all-pages --output files/okrs.xlsx

# Fetch all objectives and key results (Markdown format)
docker run --rm -v $(pwd):/app productplan-api --endpoint okrs --all-pages --output-format markdown --output files/okrs.md

# Custom filters and options
docker run --rm -v $(pwd):/app productplan-api \
  --endpoint idea-forms \
  --page 1 \
  --page-size 100 \
  --output files/custom_filename.xlsx \
  --filter name "Feature Request" \
  --filter channel "Sales"
```

**Note:** The script automatically creates the `files/` directory if it doesn't exist.

## Available Options

### Make Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `OUTPUT` | Output filename | files/productplan_data.xlsx |
| `PAGE` | Page number | 1 |
| `PAGE_SIZE` | Number of items per page | 200 |
| `ALL_PAGES` | Fetch all pages | true |
| `FILTERS` | Space-separated key:value pairs | (none) |
| `LOCATION_STATUS` | Filter ideas by location | not_archived |
| `IDEA_STATUS` | Include ideas with "Ignore" status | (none - excludes "Ignore") |
| `OBJECTIVE_STATUS` | Filter objectives by status | active |
| `OUTPUT_FORMAT` | Output format for OKRs | excel |
| `OUTPUT_TYPE` | SLA storage type | auto |

### Docker Command Options

When using Docker directly (not recommended - use `make` commands instead):

- `--endpoint`: API endpoint to query (available: 'ideas', 'teams', 'idea-forms', 'okrs', 'sla-init', 'sla-update')
- `--page`: Page number (default: 1)
- `--page-size`: Number of items per page (default: 200, max: 500)
- `--filter`: Filter results (can be used multiple times with KEY VALUE pairs)
- `--output`: Output filename (default: files/productplan_data.xlsx)
- `--all-pages`: Fetch all pages of results automatically (ignores the --page parameter)
- `--location-status`: Filter ideas by location status (available: 'all', 'visible', 'hidden', 'archived', 'not_archived'; default: not_archived)
- `--idea-status`: Include ideas with "Ignore" status (available: 'all'; default: None - excludes "Ignore" status)
- `--objective-status`: Filter objectives by status (available: 'active', 'all'; default: active)
- `--output-format`: Output format for OKRs (available: 'excel', 'markdown'; default: excel)
- `--output-type`: Storage type for SLA tracking (available: 'auto', 'excel', 'sheets'; default: auto)

**Note:** API token is loaded from `env/.env` file (PRODUCTPLAN_API_TOKEN variable)

## Filtering

### Available Filters for Ideas Endpoint

- id, name, description, channel, customer, opportunities_count, source_name, source_email, location_status
- Enhanced processing automatically fetches detailed information for each idea including:
  - Created and updated timestamps (created_at, updated_at)
  - Custom dropdown fields with their selected values
  - Tags, opportunity IDs, and idea form references
  - All custom fields are flattened into separate Excel columns for easy analysis
- Default behavior excludes archived ideas (use LOCATION_STATUS=all to include them)

### Available Filters for Teams Endpoint

- id
- name

### Available Filters for Idea Forms Endpoint

- Endpoint supports pagination and filtering (specific filters may vary based on your ProductPlan configuration)
- Enhanced processing automatically fetches detailed information for each form including:
  - Form title, instructions, enabled status, timestamps
  - Custom text fields with labels
  - Custom dropdown fields with labels and allowed values
  - All custom fields are flattened into separate Excel columns for easy analysis

### OKRs (Objectives and Key Results) Endpoint

- **Status Filtering**: Use `OBJECTIVE_STATUS=active` (default) to get only active objectives, or `OBJECTIVE_STATUS=all` to include all objectives
- **Output Formats**: Choose between Excel (`OUTPUT_FORMAT=excel`) or Markdown (`OUTPUT_FORMAT=markdown`) output
- **Team Resolution**: Automatically resolves team IDs to team names for both objectives and key results
- **Data Structure**: 
  - Excel format: Flattened rows with one row per key result (or one row per objective if no key results)
  - Markdown format: Structured document with H2 objective headings, H3 team and key results sections
- **Column Order (Excel)**: status, team_name, objective_name, objective_description, key_result_name, key_result_target, key_result_current, key_result_progress, objective_id, key_result_id

## Team Columns on Ideas Data

When fetching ideas data, columns for each team are automatically added. For each idea, a column will be added for each team with a value of 1 if the team is assigned to the idea, and 0 if not.

## Custom Text Field Extraction

When fetching ideas data, any custom text fields are automatically extracted and added as separate columns. The script:

1. Identifies all unique custom text field labels across all ideas
2. Creates a new column for each unique label with the prefix "Custom: "
3. Populates each column with the corresponding value for each idea

For example, if your `custom_text_fields` column contains data like:
```
[{'label': 'Problem to be solved', 'value': 'One authentication point for all products'}, {'label': 'Success criteria', 'value': 'Reduced login failures by 50%'}]
```

The exported Excel file will include two additional columns:
- "Custom: Problem to be solved" with value "One authentication point for all products"
- "Custom: Success criteria" with value "Reduced login failures by 50%"

This happens automatically for any number of custom text fields present in your data, with no configuration required.

## Markdown Export for OKRs

When using `OUTPUT_FORMAT=markdown`, the tool generates a structured Markdown document perfect for documentation, reports, and team reviews:

### Markdown Structure

```markdown
# Objectives and Key Results

## Objective Name
Brief description of the objective.

### Team
Team Name

### Key Results
- Key result description (target: value) - Current: X | Progress: Y%
- Another key result (target: 100%) - Current: 75% | Progress: 75%

## Another Objective

### Key Results
No key results
```

### Key Features

- **Clean Headers**: Each objective gets an H2 heading without team names in parentheses
- **Team Sections**: Dedicated H3 "Team" section for clear team attribution
- **Target Format**: Targets appear in parentheses for easy scanning: `(target: 25%)`
- **Progress Details**: Current values and progress shown after targets
- **No Key Results Handling**: Clear "No key results" message when appropriate
- **Professional Format**: Perfect for stakeholder reports, team documentation, and quarterly reviews

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

3. **Missing URL Prefix**:
   - Error: "PRODUCTPLAN_URL_PREFIX is required"
   - Solution: Set `PRODUCTPLAN_URL_PREFIX` in `env/.env`
   - Example: `PRODUCTPLAN_URL_PREFIX=https://app.productplan.com/discovery/ideas/`

4. **Google Sheets Configuration Error**:
   - Error: "Partial Google Sheets configuration detected"
   - Solution: Either set ALL three Google Sheets variables or NONE
   - Required: GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME

5. **Permission Error When Writing Output**:
   - Check that the current directory is writable
   - Try specifying a different output path with the OUTPUT parameter

6. **Docker Not Running**:
   - Make sure Docker Desktop is running on your machine
   - Try restarting Docker if you're having issues

### Getting Help

For more information:
- Run `make help` to see all available commands and options
- Refer to the ProductPlan API documentation for endpoint details
- Check the User Guide document for detailed usage examples