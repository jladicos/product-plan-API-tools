FROM python:3.9-slim

WORKDIR /app

# Install build dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
	gcc \
	g++ \
	python3-dev \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package and tests
COPY productplan_api_tools/ productplan_api_tools/
COPY tests/ tests/

# Create an empty token file if needed (will be overwritten by volume mount)
RUN touch token.txt

# Set entrypoint to use new package
ENTRYPOINT ["python", "-m", "productplan_api_tools"]

# Default command (can be overridden)
CMD ["--help"]