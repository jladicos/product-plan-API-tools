# ProductPlan API Client

A flexible Python script to fetch data from the ProductPlan API and export it to Excel format, designed to run in a Docker container.

## Features

- Fetch ideas from ProductPlan API
- Fetch teams from ProductPlan API
- Export data to Excel
- Filter results using command-line arguments
- Pagination support
- Token-based authentication
- Automatic team columns on ideas exports (1 if assigned, 0 if not)
- Docker containerization for easy deployment

## Setup

### Prerequisites

- Docker installed on your system
- A valid ProductPlan API token

### Getting Started

1. Clone this repository:
   ```
   git clone <repository-url>
   cd productplan-api-client
   ```

2. Create a `token.txt` file with your ProductPlan API token:
   ```
   echo "YOUR-BEARER-TOKEN-HERE" > token.txt
   ```

3. Build the Docker image:
   ```
   docker build -t productplan-api .
   ```

## Usage

### Basic Usage

To get started and fetch data from the ProductPlan API, run:

```bash
# Fetch the first page of ideas (includes team columns)
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas

# Fetch the first page of teams
docker run --rm -v $(pwd):/app productplan-api --endpoint teams
```

This will fetch the first page of data and save it to `output.xlsx` in the current directory.

> **Important:** Running the container without any arguments will display the help text, not fetch data. You must explicitly specify an endpoint (e.g., `--endpoint ideas` or `--endpoint teams`) to retrieve data.

#### Fetching All Data

To fetch all items across all pages:

```bash
# Fetch all ideas (includes team columns)
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --all-pages

# Fetch all teams
docker run --rm -v $(pwd):/app productplan-api --endpoint teams --all-pages
```

This will automatically paginate through all available data, combine it, and save it to `output.xlsx`.

### Team Columns on Ideas Data

When fetching ideas data, columns for each team are automatically added. For each idea, a column will be added for each team with a value of 1 if the team is assigned to the idea, and 0 if not.

This feature:
1. Fetches all teams first to build a mapping of team IDs to team names
2. Then fetches the ideas data
3. For each idea, adds a column for each team with 1 or 0 based on team assignment
4. Keeps the original team_ids column in the output

### Command-line Arguments

You can pass various command-line arguments to customize the API request:

```bash
docker run --rm -v $(pwd):/app productplan-api \
  --endpoint ideas \
  --page 1 \
  --page-size 100 \
  --output custom_filename.xlsx \
  --filter name "Feature Request" \
  --filter channel "Sales"
```

#### Available Arguments

- `--endpoint`: API endpoint to query (available: 'ideas', 'teams')
- `--token-file`: File containing the API token (default: token.txt)
- `--page`: Page number (default: 1)
- `--page-size`: Number of items per page (default: 200, max: 500)
- `--filter`: Filter results (can be used multiple times with KEY VALUE pairs)
- `--output`: Output filename (default: output.xlsx)
- `--all-pages`: Fetch all pages of results automatically (ignores the --page parameter)

### Filtering

You can filter the API results by adding one or more `--filter` arguments.

#### Filtering Ideas
```bash
docker run --rm -v $(pwd):/app productplan-api \
  --endpoint ideas \
  --filter name "New Feature" \
  --filter customer "Acme Inc"
```

Available filter attributes for the ideas endpoint:
- id
- name
- description
- channel
- customer
- opportunities_count
- source_name
- source_email
- location_status

#### Filtering Teams
```bash
docker run --rm -v $(pwd):/app productplan-api \
  --endpoint teams \
  --filter name "Product Team"
```

Available filter attributes for the teams endpoint:
- id
- name

## Troubleshooting

### Common Issues

1. **Authentication Failed (401)**:
   - Verify that your token in `token.txt` is correct and not expired
   - Ensure there are no extra spaces or newlines in the token file

2. **Permission Error When Writing Output**:
   - Check that the current directory is writable by Docker
   - Use the absolute path for the output file

3. **Rate Limiting**:
   - If you encounter rate limiting, try reducing the request frequency

### Getting Help

For more information about the ProductPlan API, refer to their official documentation.