# ProductPlan API Client

A flexible Python script to fetch data from the ProductPlan API and export it to Excel format, designed to run in a Docker container with simplified `make` commands.

## Features

- Fetch ideas from ProductPlan API
- Fetch teams from ProductPlan API
- Fetch idea forms from ProductPlan API with detailed information (includes custom fields, instructions, etc.)
- **NEW: Fetch objectives and key results (OKRs) from ProductPlan API**
- Export data to Excel format
- **NEW: Export OKR data to Markdown format for documentation and reporting**
- Filter results using command-line arguments
- **NEW: Filter objectives by status (active/all)**
- Pagination support
- Token-based authentication
- Automatic team columns on ideas exports (1 if assigned, 0 if not)
- **NEW: Automatic team name resolution for objectives and key results**
- Automatic extraction of custom text fields into separate columns
- Simplified `make` commands for ease of use
- Docker containerization for easy deployment
- **Organized file output** - All generated files saved to `files/` directory by default

## File Organization

All generated files are automatically saved to the `files/` directory:
- `files/ideas.xlsx` - Ideas data with custom fields and team assignments
- `files/teams.xlsx` - Team information
- `files/idea-forms.xlsx` - Idea form definitions
- `files/okrs.xlsx` or `files/okrs.md` - Objectives and key results data
- The `files/` directory is git-ignored to keep your repository clean
- The script automatically creates this directory if it doesn't exist

## Setup

### Prerequisites

- Docker installed on your system
- Make installed on your system (pre-installed on macOS and Linux)
- A valid ProductPlan API token

### Getting Started

1. Clone this repository:
   ```
   git clone https://github.com/jladicos/product-plan-API-tools
   cd productplan-api-client
   ```

2. Run the setup script:
   ```
   ./setup.sh
   ```
   
   The setup script will:
   - Check for Docker and Make installation
   - Help you create a token.txt file with your API token
   - Build the Docker image
   - Provide quick-start instructions

## Testing

This project includes a comprehensive test suite with 137 total tests ensuring reliability and preventing regressions.

### Test Types

**Unit Tests** - Test individual components in isolation (127 tests):
- Test all package components (resources, exporters, utils, CLI)
- Mock external dependencies (HTTP requests, file I/O)
- Fast execution (~0.5 seconds)
- 100% coverage of architecture
- Run automatically on every change
- Run with: `make test`

**Smoke Tests (Real API)** - Verify API contracts haven't changed (10 tests):
- Hit actual ProductPlan API endpoints
- Test authentication, teams, ideas, OKRs, idea forms, objective mapping
- Require valid `token.txt` file
- Run occasionally (before releases, after API changes)
- Skip gracefully if token file is missing
- Run with: `make test-smoke`

### Running Tests

```bash
# Run unit tests (recommended for development)
make test

# Run smoke tests against real API (requires token.txt)
make test-smoke

# Run all tests (unit + smoke)
make test-all
```

### Test Results Summary

- **Unit Tests**: 127/127 passing (100%)
- **Smoke Tests**: 10/10 passing (100%)
- **Total Tests**: 137/137 passing (100%)
- **All Tests Verified**: ✅ October 31, 2024

### Test Coverage

The test suite provides comprehensive coverage:
- ✅ All API endpoints (ideas, teams, OKRs, idea forms)
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

# Filter objectives by status
make okrs OBJECTIVE_STATUS=all  # Include inactive objectives
make okrs OBJECTIVE_STATUS=active  # Active objectives only (default)
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
| `TOKEN_FILE` | File containing the API token | token.txt |
| `ALL_PAGES` | Fetch all pages | true |
| `FILTERS` | Space-separated key:value pairs | (none) |
| `OBJECTIVE_STATUS` | Filter objectives by status | active |
| `OUTPUT_FORMAT` | Output format for OKRs | excel |

### Docker Command Options

- `--endpoint`: API endpoint to query (available: 'ideas', 'teams', 'idea-forms', 'okrs')
- `--token-file`: File containing the API token (default: token.txt)
- `--page`: Page number (default: 1)
- `--page-size`: Number of items per page (default: 200, max: 500)
- `--filter`: Filter results (can be used multiple times with KEY VALUE pairs)
- `--output`: Output filename (default: files/productplan_data.xlsx)
- `--all-pages`: Fetch all pages of results automatically (ignores the --page parameter)
- `--objective-status`: Filter objectives by status (available: 'active', 'all'; default: active)
- `--output-format`: Output format for OKRs (available: 'excel', 'markdown'; default: excel)

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

1. **Authentication Failed (401)**:
   - Verify that your token in `token.txt` is correct and not expired
   - Ensure there are no extra spaces or newlines in the token file

2. **Permission Error When Writing Output**:
   - Check that the current directory is writable
   - Try specifying a different output path with the OUTPUT parameter

3. **Docker Not Running**:
   - Make sure Docker Desktop is running on your machine
   - Try restarting Docker if you're having issues

### Getting Help

For more information:
- Run `make help` to see all available commands and options
- Refer to the ProductPlan API documentation for endpoint details
- Check the User Guide document for detailed usage examples