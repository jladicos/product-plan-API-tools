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

# Copy script
COPY productplan_api.py .

# Create an empty token file if needed (will be overwritten by volume mount)
RUN touch token.txt

# Make script executable
RUN chmod +x productplan_api.py

# Set entrypoint
ENTRYPOINT ["python", "productplan_api.py"]

# Default command (can be overridden)
CMD ["--help"]