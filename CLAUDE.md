# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-driven cybersecurity automation platform using the Model Context Protocol (MCP). The system processes security events through AI-powered analysis and routes them to specialized MCP servers for threat intelligence, incident management, and endpoint investigation. It supports both desktop (Tkinter) and web (FastAPI) interfaces with Kafka streaming, S3 automation, and multi-cloud AI provider support.

## Architecture

The system uses a **client-server architecture** with AI-driven event processing:

```
Event Input → AI Analysis → MCP Server Routing → Cybersecurity Actions
    ↓             ↓              ↓                    ↓
File/Kafka   EventProcessor   HTTP Client        VirusTotal/ServiceNow/etc
```

### Core Components Architecture

- **Event Processing Pipeline**: 
  - `EventParser` → standardizes events into `SecurityEventTaxonomy`
  - `EventProcessor` → AI-powered analysis and action determination  
  - `MCPClient` → HTTP communication with MCP servers
  - `AIProvider` → abstraction layer supporting AWS Bedrock, Google Vertex AI, Gemini

- **Client Applications**:
  - Desktop: Tkinter GUI (`src/client/desktop_app.py`)
  - Web: FastAPI app (`src/client/web_app.py`) with WebSocket support
  - Both share the same `EventProcessor` core

- **MCP Server Ecosystem**: 5 FastAPI servers (ports 8001-8005) with `/meta` capability discovery

### AI Provider Abstraction

The system supports multiple AI providers through `AIProviderFactory`:
- **AWS Bedrock**: Claude 3.5 Sonnet (default)
- **Google Vertex AI**: Claude 3.5 Sonnet 
- **Google Vertex AI Gemini**: Gemini 1.5 Pro
- **Rule-based fallback** when AI providers fail

## Development Environment Setup

### Package Management

This project uses **UV** as the Python package manager alongside traditional pip:

```bash
# UV is the modern Python package manager (faster than pip)
# Install dependencies with UV (if available)
uv pip install -r requirements.txt
uv pip install -e .                             # Install in development mode

# Traditional pip installation (fallback)
pip install -r requirements.txt
pip install -e .

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

### Environment Variables

Key environment variables for configuration:
```bash
# AWS Bedrock (primary AI provider)
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Google Vertex AI (alternative provider)
export GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
export GCP_PROJECT_ID=your-project-id

# Debug mode
export DEBUG=1                                   # Enable detailed logging
export PYTHONPATH=.                             # For local development
```

## Common Development Commands

### Starting the Application

```bash
# Desktop application (full workflow)
python launch_servers.py    # Start all MCP servers (ports 8001-8005)
python main.py              # Start Tkinter GUI (separate terminal)

# Web application (integrated)
python launch_web_app.py    # Start servers + web app together
# OR
python web_main.py          # Web app only (if servers already running)

# Individual server testing
python src/servers/virustotal_server.py  # Port 8001
python src/servers/servicenow_server.py  # Port 8002
# ... etc for ports 8003-8005
```

The web application runs on `http://localhost:8080` with WebSocket support for real-time updates.

### Web Application Features

The FastAPI web app (`src/client/web_app.py`) provides:
- **File Upload Interface**: Drag-and-drop for JSON/CSV event files
- **Real-time Processing**: WebSocket updates during event analysis
- **AI Chat Interface**: Natural language prompts with streaming responses
- **S3 Integration**: Automatic bucket monitoring and file processing
- **Event History**: View past analyses and results
- **API Documentation**: Auto-generated docs at `http://localhost:8080/docs`

### Testing

```bash
# Run all tests (recommended)
python run_tests.py

# Pytest options
pytest                                           # All tests
pytest -v                                        # Verbose output
pytest -m unit                                   # Unit tests only
pytest -m integration                            # Integration tests only
pytest tests/test_client/test_event_processor.py # Specific file
pytest tests/test_servers/                       # Specific directory
pytest --maxfail=5                              # Stop after 5 failures

# Test with async support (configured in pytest.ini)
pytest --asyncio-mode=auto                      # Explicit async mode
```

### Code Quality and Linting

```bash
# This project currently uses basic Python standards
# No specific linting tools (ruff, black, flake8) are configured
# When adding code quality tools, consider:

# Install and run ruff (recommended for new Python projects)
pip install ruff
ruff check .                                     # Check for issues
ruff format .                                    # Format code

# Install and run black (Python formatter)
pip install black
black .                                          # Format all Python files

# Install and run mypy (type checking)
pip install mypy
mypy src/                                        # Type check source code
```

### Server Testing and API Validation

```bash
# Test server endpoints (ensure servers are running first)
curl http://0.0.0.0:8001/meta                   # Get capabilities
curl http://0.0.0.0:8001/docs                   # OpenAPI documentation
curl -H "X-API-Key: test" -X POST http://0.0.0.0:8001/ip_report \
  -d '{"ip": "8.8.8.8"}'                        # Test VirusTotal endpoint
```

### GCP Deployment

```bash
# Simple deployment for development/testing
./scripts/deploy_to_gcp.sh                      # Deploy to GCP VM

# Clean up resources when done
./scripts/cleanup_gcp.sh                        # Remove all GCP resources
```

### Kafka/Redpanda Messaging

```bash
# Local messaging infrastructure
./scripts/start_messaging_infra.sh              # Start Redpanda cluster
./scripts/create_topics.sh                      # Create Kafka topics
./scripts/publish_sample_events.sh              # Send test events
./scripts/stop_messaging_infra.sh               # Clean shutdown

# Docker Compose options
docker-compose -f docker-compose.redpanda.yml up -d     # Redpanda only
docker-compose -f deployment/docker-compose.minimal.yml up -d  # Essential services
```

## Configuration Architecture

### Centralized Configuration (`src/config/settings.py`)

The `AppConfig` class manages all system configuration:

```python
class AppConfig:
    def __init__(self):
        self.mcp_servers = {...}      # MCP server definitions
        self.ai_config = {...}        # AI provider settings  
        self.kafka_config = {...}     # Kafka/Redpanda settings
        self.bucket_config = {...}    # S3 automation settings
```

### MCP Server Configuration Pattern

Each server follows this structure in `settings.py`:
```python
"server_name": {
    "base_url": "http://0.0.0.0:PORT",
    "capabilities": ["endpoint1", "endpoint2"],  # From /meta endpoint
    "auth_headers": {"Header-Name": "value"}
}
```

Authentication by server type:
- **VirusTotal/Trellix**: `X-API-Key` header
- **ServiceNow**: `Authorization` header (Basic/Bearer)  
- **CyberReason**: `Authorization` Bearer token
- **Custom REST**: Configurable per API

## AI Provider System

### Multi-Provider Architecture

The system uses `AIProviderFactory` to create provider instances:
- **AWS Bedrock**: Claude 3.5 Sonnet (default)
- **Google Vertex AI**: Claude 3.5 Sonnet via GCP
- **Google Vertex AI Gemini**: Gemini 1.5 Pro via GCP  
- **Rule-based fallback**: When AI providers fail

Provider selection in `settings.py`:
```python
ai_config = {
    "provider": "aws_bedrock",  # or "google_vertex", "google_vertex_gemini"
    "fallback_to_rules": True,  # Enable rule-based fallback
    # Provider-specific configs...
}
```

### AI Analysis Pipeline

The `EventProcessor.analyze_with_ai()` method:
1. Creates analysis prompt from event + user input
2. Calls selected AI provider
3. Parses AI response for MCP server actions
4. Falls back to rules if AI fails

Key integration points:
- `src/client/ai_provider.py` - Provider abstractions
- `src/client/event_processor.py` - AI analysis logic
- Fallback logic in `RuleBasedFallback` class

## Event Processing System

### SecurityEventTaxonomy Structure

The `EventParser` converts various input formats into a standardized `SecurityEventTaxonomy`:

```python
class SecurityEventTaxonomy:
    # Core identification
    event_id: str
    timestamp: str
    event_type: str        # malware, network_anomaly, authentication, etc
    severity: str          # critical, high, medium, low
    
    # Indicators of Compromise
    indicators: Dict       # IPs, domains, hashes, URLs
    
    # Asset information  
    affected_assets: List  # hostnames, endpoints
    
    # Additional context
    description: str
    raw_data: Dict        # Original event data
```

### Multi-Format Input Support

The system processes events from multiple sources:
- **File uploads**: JSON, CSV, syslog formats via desktop/web UI
- **Kafka streams**: Real-time event ingestion from topics
- **S3 automation**: Automatic processing of uploaded files

S3 bucket workflow (`bucket_client.py` + `bucket_monitor.py`):
```
s3://ai-soar/unprocessed/ → Auto-detect → Process → s3://ai-soar/processed/
                                           ↓
                            Real-time WebSocket updates to web UI
```

## MCP Server Ecosystem

### Server Pattern and `/meta` Endpoint

All MCP servers follow a consistent FastAPI pattern:

```python
from fastapi import FastAPI, HTTPException, Depends
from .auth import get_auth_headers  # Custom dependency injection

app = FastAPI(title="Server Name")

@app.get("/meta")
async def get_capabilities():
    return {"capabilities": ["endpoint1", "endpoint2"], "server": "name"}

@app.post("/endpoint1")  
async def endpoint1(request: RequestModel, auth: dict = Depends(get_auth_headers)):
    # Implementation with proper error handling
    pass
```

Each server runs independently and exposes:
- `/meta` - Capability discovery
- `/docs` - Auto-generated OpenAPI documentation  
- Custom endpoints based on cybersecurity function

### Server-Specific Functions

1. **VirusTotal** (8001): `ip_report`, `domain_report` - IOC reputation lookup
2. **ServiceNow** (8002): `create_record`, `get_record` - Incident/task management
3. **CyberReason** (8003): `get_pylum_id`, `check_terminal_status` - Endpoint investigation
4. **Custom REST** (8004): `custom_enrichment` - Generic API wrapper with configurable endpoints
5. **Trellix Cloud IVX** (8005): `lookup_hashes`, `analyse_url`, `analyse_file` - Advanced malware analysis and threat intelligence

## Development Patterns

### Async/Await Architecture

The entire system is built on async patterns:
- `EventProcessor.process_event()` - Main async processing pipeline
- `MCPClient` methods - HTTP requests with aiohttp
- FastAPI servers - Native async support
- WebSocket connections - Real-time updates in web client

### Error Handling Strategy

Multi-layer error handling:
1. **AI Provider fallback** - Rule-based analysis if AI fails
2. **MCP Client retries** - HTTP request retry logic
3. **Server-specific exceptions** - Custom error types for different failure modes
4. **User-friendly messages** - Error translation for GUI display

### Decision Logic for AI Analysis

The AI analyzes events and user prompts considering:
- **Event attributes**: IOCs, hostnames, severity levels
- **Prompt keywords**: "malicious", "ticket", "endpoint", "reputation"  
- **Conditional logic**: "if high severity", "if compromised"

Fallback logic when AI unavailable:
1. VirusTotal for IOC enrichment
2. ServiceNow tickets for high/critical severity
3. CyberReason for host-related events

## Sample Data and Testing

Test files in `sample_data/`:
- `security_events.json` - Comprehensive security events
- `security_events.csv` - Events in CSV format  
- `mixed_format_events.json` - Mixed event types
- `syslog_events.log` - Syslog format events

## Troubleshooting

### Common Development Issues

1. **MCP Server Connection Failures**
   ```bash
   # Check if all servers are running
   curl http://localhost:8001/meta  # VirusTotal
   curl http://localhost:8002/meta  # ServiceNow
   curl http://localhost:8003/meta  # CyberReason
   curl http://localhost:8004/meta  # Custom REST
   curl http://localhost:8005/meta  # Trellix Cloud IVX
   
   # Restart servers if needed
   python launch_servers.py
   ```

2. **AI Provider Authentication Errors**
   ```bash
   # Test AWS Bedrock connection
   python -c "from src.client.ai_provider import AWSBedrockProvider; print('AWS OK')"
   
   # Test Google Vertex AI connection
   python test_vertexai.py
   
   # Check environment variables
   echo $AWS_DEFAULT_REGION
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

3. **Async/Await Import Errors**
   ```bash
   # Ensure pytest-asyncio is installed
   pip install pytest-asyncio
   
   # Check pytest.ini configuration
   cat pytest.ini | grep asyncio
   ```

4. **Port Conflicts**
   ```bash
   # Check which ports are in use
   lsof -i :8001-8005
   netstat -tuln | grep -E '(8001|8002|8003|8004|8005|8080)'
   
   # Kill processes if needed
   pkill -f "uvicorn.*800[1-5]"
   ```

### Integration Testing Issues

- **Mock Server Responses**: Check `tests/conftest.py` for proper mock configurations
- **Async Test Failures**: Ensure all async functions use `await` and tests are marked with `@pytest.mark.asyncio`
- **Event Processing**: Verify `SecurityEventTaxonomy` structure matches test data

## Extending the System

### Adding New MCP Servers

1. Create `src/servers/new_server.py` following the FastAPI pattern
2. Add server config to `src/config/settings.py`
3. Update `launch_servers.py` to include new server
4. Add capability recognition in `EventProcessor` if specialized logic needed

### Custom REST API Integration  

The Custom REST server (`src/servers/custom_rest_server.py`) allows dynamic API registration:
```python
# Register new endpoint configuration
config = {
    "name": "threat_intel_api",
    "base_url": "https://api.example.com",
    "auth_headers": {"Authorization": "Bearer token"},
    "endpoints": {...}
}
```