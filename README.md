# ProductPlan API Client

A flexible Python script to fetch data from the ProductPlan API and export it to Excel format, designed to run in a Docker container with simplified `make` commands.

## Features

- Fetch ideas from ProductPlan API
- Fetch teams from ProductPlan API
- Fetch idea forms from ProductPlan API with detailed information (includes custom fields, instructions, etc.)
- Export data to Excel
- Filter results using command-line arguments
- Pagination support
- Token-based authentication
- Automatic team columns on ideas exports (1 if assigned, 0 if not)
- Automatic extraction of custom text fields into separate columns
- Simplified `make` commands for ease of use
- Docker containerization for easy deployment

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

# Fetch all data types (saved as ideas.xlsx, teams.xlsx, and idea-forms.xlsx)
make all

# See all available commands and options
make help
```

### Customizing Output Filename

```bash
# Set custom output filename
make ideas OUTPUT=my_ideas.xlsx
make teams OUTPUT=my_teams.xlsx
make idea-forms OUTPUT=my_forms.xlsx
```

### Filtering Results

Use the FILTERS parameter with key:value pairs (separate multiple filters with spaces):

```bash
# Single filter
make ideas FILTERS="name:Feature Request"

# Multiple filters
make ideas FILTERS="name:Feature Request channel:Sales"
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
```

## Usage with Direct Docker Commands

You can still use the direct Docker commands if needed:

```bash
# Fetch the first page of ideas (includes team columns)
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas

# Fetch all ideas
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --all-pages

# Fetch all teams
docker run --rm -v $(pwd):/app productplan-api --endpoint teams --all-pages

# Fetch all idea forms with detailed information
docker run --rm -v $(pwd):/app productplan-api --endpoint idea-forms --all-pages

# Custom filters and options
docker run --rm -v $(pwd):/app productplan-api \
  --endpoint idea-forms \
  --page 1 \
  --page-size 100 \
  --output custom_filename.xlsx \
  --filter name "Feature Request" \
  --filter channel "Sales"
```

## Available Options

### Make Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `OUTPUT` | Output filename | productplan_data.xlsx |
| `PAGE` | Page number | 1 |
| `PAGE_SIZE` | Number of items per page | 200 |
| `TOKEN_FILE` | File containing the API token | token.txt |
| `ALL_PAGES` | Fetch all pages | true |
| `FILTERS` | Space-separated key:value pairs | (none) |

### Docker Command Options

- `--endpoint`: API endpoint to query (available: 'ideas', 'teams', 'idea-forms')
- `--token-file`: File containing the API token (default: token.txt)
- `--page`: Page number (default: 1)
- `--page-size`: Number of items per page (default: 200, max: 500)
- `--filter`: Filter results (can be used multiple times with KEY VALUE pairs)
- `--output`: Output filename (default: output.xlsx)
- `--all-pages`: Fetch all pages of results automatically (ignores the --page parameter)

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