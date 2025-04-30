#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
	echo "Docker is not installed. Please install Docker first."
	echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
	exit 1
fi

# Check if token.txt exists
if [ ! -f token.txt ]; then
	echo "Token file not found. Please enter your ProductPlan API token:"
	read -r token
	echo "$token" > token.txt
	echo "Token saved to token.txt"
else
	echo "Using existing token.txt file"
fi

# Build Docker image
echo "Building Docker image..."
docker build -t productplan-api .

echo ""
echo "Setup complete! You can now run the script with:"
echo "docker run --rm -v \$(pwd):/app productplan-api"
echo ""
echo "For more options, run:"
echo "docker run --rm productplan-api --help"