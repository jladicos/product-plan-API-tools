FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script and token file
COPY productplan_api.py .
COPY token.txt .

# Make script executable
RUN chmod +x productplan_api.py

# Set entrypoint
ENTRYPOINT ["python", "productplan_api.py"]

# Default command (can be overridden)
CMD ["--help"]