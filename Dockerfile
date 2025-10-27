# Dockerfile for running tests locally
# Replicates GitHub Actions test environment

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (including build tools for C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy test requirements first (for better caching)
COPY tests/requirements_test.txt tests/

# Install Python dependencies
RUN pip install --no-cache-dir -r tests/requirements_test.txt pytest-cov

# Copy the entire project
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Default command: run tests with coverage
CMD ["pytest", "--cov=custom_components.meteolux", "--cov-report=xml", "--cov-report=term", "--cov-report=html", "-v", "tests/"]
