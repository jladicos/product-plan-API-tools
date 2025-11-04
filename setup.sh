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

# Check for env/.env file
if [ ! -f env/.env ]; then
	echo "⚠️  No env/.env file found."
	echo "   Would you like to create it now from the sample? (y/n)"
	read -r create_env
	if [[ "$create_env" == "y" || "$create_env" == "Y" ]]; then
		# Copy sample to env/.env
		cp env/.env.sample env/.env

		echo "✅ env/.env created from sample."
		echo ""
		echo "   Please enter your ProductPlan API token:"
		read -r token

		# Replace the placeholder with actual token
		if [[ "$OSTYPE" == "darwin"* ]]; then
			# macOS uses BSD sed
			sed -i '' "s|PRODUCTPLAN_API_TOKEN=your_api_token_here|PRODUCTPLAN_API_TOKEN=$token|" env/.env
		else
			# Linux uses GNU sed
			sed -i "s|PRODUCTPLAN_API_TOKEN=your_api_token_here|PRODUCTPLAN_API_TOKEN=$token|" env/.env
		fi

		echo "✅ API token configured in env/.env"
		echo ""
		echo "   You can edit env/.env to configure additional options like Google Sheets."
	else
		echo "⚠️  You will need to create env/.env from env/.env.sample before using the client."
		echo "   Copy the file and fill in your ProductPlan API token:"
		echo "   cp env/.env.sample env/.env"
	fi
else
	echo "✅ env/.env found."
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
echo "3. Initialize SLA tracking:"
echo "   make sla-init"
echo
echo "4. See all available commands:"
echo "   make help"
echo
echo "For more details, run: make help"
echo
