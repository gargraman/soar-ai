# Multi-stage Dockerfile for MCP Cybersecurity Platform

# Stage 1: Base Python environment
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: MCP Servers
FROM base as mcp-servers

# Copy source code
COPY src/ ./src/
COPY sample_data/ ./sample_data/

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/config

# Copy configuration
COPY deployment/config/ ./config/

# Expose ports for all MCP servers
EXPOSE 8001 8002 8003 8004 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/meta || exit 1

# Default command to start all servers
CMD ["python", "-m", "src.deployment.start_servers"]

# Stage 3: Web Application
FROM base as web-app

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/config

# Copy configuration
COPY deployment/config/ ./config/

# Expose web application port
EXPOSE 8080

# Health check for web application
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the web application
CMD ["python", "web_main.py"]