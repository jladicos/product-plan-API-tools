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
| `make all` | Get both ideas and teams |
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

## Advanced Usage

### Custom Commands

For maximum flexibility, use the `custom` command:

```bash
make custom ENDPOINT=ideas OUTPUT=custom.xlsx PAGE_SIZE=500
```

### All Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `OUTPUT` | Output filename | productplan_data.xlsx |
| `PAGE` | Page number | 1 |
| `PAGE_SIZE` | Number of items per page | 200 |
| `TOKEN_FILE` | File containing the API token | token.txt |
| `ALL_PAGES` | Fetch all pages | true |
| `FILTERS` | Space-separated key:value pairs | (none) |

## Using Direct Docker Commands

You can still use the direct Docker commands if needed:

```bash
docker run --rm -v $(pwd):/app productplan-api --endpoint ideas --all-pages --output output.xlsx
```

## Troubleshooting

### Common Issues

1. **Authentication Failed (401)**:
   - Verify that your token in `token.txt` is correct and not expired
   - Ensure there are no extra spaces or newlines in the token file

2. **Permission Error When Writing Output**:
   - Make sure you're running the command in a directory where you have write permissions
   - Try specifying a different output path: `make ideas OUTPUT=/path/to/output.xlsx`

3. **Docker Not Running**:
   - Make sure Docker Desktop is running on your machine
   - Try restarting Docker if you're having issues

4. **"make: command not found" Error**:
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