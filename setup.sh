#!/bin/bash

# ProductPlan API Client Setup Script

echo "ProductPlan API Client - Setup"
echo "============================="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
	echo "❌ Docker is not installed. Please install Docker first."
	echo "   Visit https://docs.docker.com/get-docker/ for installation instructions."
	exit 1
else
	echo "✅ Docker is installed."
fi

# Check if make is installed
if ! command -v make &> /dev/null; then
	echo "❌ Make is not installed. Please install Make first."
	if [[ "$OSTYPE" == "darwin"* ]]; then
		echo "   For macOS, you can install it with Homebrew: brew install make"
	elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
		echo "   For Ubuntu/Debian: sudo apt-get install make"
		echo "   For Fedora/RHEL: sudo dnf install make"
	fi
	exit 1
else
	echo "✅ Make is installed."
fi

# Check for token.txt
if [ ! -f token.txt ]; then
	echo "⚠️ No token.txt file found."
	echo "   Would you like to create it now? (y/n)"
	read -r create_token
	if [[ "$create_token" == "y" || "$create_token" == "Y" ]]; then
		echo "   Please enter your ProductPlan API token:"
		read -r token
		echo "$token" > token.txt
		echo "✅ token.txt created."
	else
		echo "⚠️ You will need to create a token.txt file with your API token before using the client."
	fi
else
	echo "✅ token.txt found."
fi

# Build Docker image
echo
echo "Building Docker image..."
if docker build -t productplan-api .; then
	echo "✅ Docker image built successfully."
else
	echo "❌ Failed to build Docker image."
	exit 1
fi

echo
echo "Setup complete! 🎉"
echo
echo "Quick Start Guide:"
echo "-----------------"
echo "1. Get all ideas:"
echo "   make ideas"
echo
echo "2. Get all teams:"
echo "   make teams"
echo
echo "3. Get both ideas and teams:"
echo "   make all"
echo
echo "4. See all available commands:"
echo "   make help"
echo
echo "For more details, run: make help"
echo