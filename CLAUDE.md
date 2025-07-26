# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-driven cybersecurity automation platform using the Model Context Protocol (MCP). The system consists of a desktop GUI client that processes security events and routes them to various MCP servers for threat intelligence, incident management, and endpoint investigation.

## Architecture

The project follows a client-server architecture:

- **Desktop Client** (`src/client/`): Tkinter GUI application with AI-powered event processing
- **MCP Servers** (`src/servers/`): Four FastAPI servers providing cybersecurity services
- **Event Processing**: Claude 3.5 Sonnet via AWS Bedrock for intelligent analysis and routing
- **Configuration**: Centralized settings in `src/config/settings.py`

### Key Components

- `main.py`: Entry point for the desktop application
- `launch_servers.py`: Utility to start all MCP servers simultaneously
- `src/client/desktop_app.py`: Main GUI application with event upload and processing
- `src/client/event_processor.py`: AI-powered event analysis and MCP server routing
- `src/client/mcp_client.py`: HTTP client for communicating with MCP servers

### MCP Servers

1. **VirusTotal Server** (port 8001): IP/domain reputation lookups
2. **ServiceNow Server** (port 8002): Incident and task management
3. **CyberReason Server** (port 8003): Endpoint status and threat detection
4. **Custom REST Server** (port 8004): Generic REST API wrapper

## Common Development Commands

### Starting the Application
```bash
# Start all MCP servers
python launch_servers.py

# Run the desktop application (in a separate terminal)
python main.py
```

### Testing
```bash
# Run all tests using the test runner (recommended)
python run_tests.py

# Run all tests directly with pytest
pytest

# Run with verbose output
pytest -v

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run specific test file
pytest tests/test_client/test_event_processor.py

# Run tests in a specific directory
pytest tests/test_servers/

# Run tests with maximum failures limit
pytest --maxfail=5
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r tests/requirements.txt

# Install all dependencies (main + test)
pip install -r requirements.txt -r tests/requirements.txt
```

### Working Directory Context
When working on MCP servers, note that you're currently in `/src/servers/`. Key files are:
- Project root: `../../` (contains main.py, launch_servers.py, requirements.txt)
- Client code: `../client/` 
- Configuration: `../config/settings.py`
- Tests: `../../tests/`

## Configuration

### MCP Server Configuration
Edit `src/config/settings.py` to modify:
- Server URLs and ports
- Authentication headers for external APIs
- AI model configuration (AWS Bedrock/Claude settings)
- Kafka configuration for streaming events

### Authentication Setup
Each MCP server requires specific authentication:
- **VirusTotal**: `X-API-Key` header
- **ServiceNow**: `Authorization` header (Basic/Bearer)
- **CyberReason**: `Authorization` Bearer token
- **Custom REST**: Configurable per API

## AI Provider Configuration

The system supports multiple AI providers for event analysis:

### Supported Providers
1. **AWS Bedrock** (default): Claude 3.5 Sonnet via AWS Bedrock
2. **Google Vertex AI**: Claude 3.5 Sonnet via Google Cloud Vertex AI

### Provider Configuration
Edit `src/config/settings.py` to select AI provider:

```python
ai_config = {
    "provider": "aws_bedrock",  # or "google_vertex"
    "aws_bedrock": {
        "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "region": "us-east-1",
        "max_tokens": 2000,
        "temperature": 0.1
    },
    "google_vertex": {
        "model": "claude-3-5-sonnet@20241022",
        "project_id": "your-gcp-project-id",
        "location": "us-central1",
        "max_tokens": 2000,
        "temperature": 0.1
    },
    "fallback_to_rules": True
}
```

### Authentication Setup
- **AWS Bedrock**: Configure AWS credentials (`aws configure` or IAM roles)
- **Google Vertex AI**: Set up Google Cloud credentials and enable Vertex AI API

## Event Processing Logic

The AI agent analyzes security events and user prompts to determine appropriate actions:

### Decision Factors
- **Event attributes**: IOCs (IPs, domains, hashes), hostnames, severity levels
- **Prompt keywords**: "malicious", "ticket", "endpoint", "reputation"
- **Conditional logic**: "if high severity", "if compromised"

### Fallback Logic
When no specific servers are mentioned or AI providers are unavailable:
1. VirusTotal for IOC enrichment
2. ServiceNow tickets for high/critical severity events
3. CyberReason for host-related events

## Sample Data

Test the application with provided sample files:
- `sample_data/security_events.json`: Comprehensive security events
- `sample_data/security_events.csv`: Events in CSV format
- `sample_data/mixed_format_events.json`: Mixed event types
- `sample_data/syslog_events.log`: Syslog format events

## Development Notes

- The application uses FastAPI for MCP servers with automatic OpenAPI documentation
- Event parsing supports multiple formats: JSON, CSV, and syslog
- AI analysis provides detailed reasoning and audit trails via configurable providers
- All servers expose `/meta` endpoints for capability discovery
- Configuration supports both file-based and environment variable loading
- AI provider abstraction allows easy switching between AWS Bedrock and Google Vertex AI
- Automatic fallback to rule-based analysis when AI providers are unavailable

### Code Quality and Standards
- All async functions use proper `async`/`await` patterns
- FastAPI dependency injection is used for configuration and authentication
- Tests use pytest with asyncio support and proper mocking
- Configuration is centralized in `src/config/settings.py`
- Error handling includes specific exceptions for different failure modes

### Development Workflow
1. Make changes to relevant files
2. Run tests with `python run_tests.py` or `pytest`
3. Test servers individually by starting them with `python <server_name>.py`
4. Test full system by running `python ../../launch_servers.py` then `python ../../main.py`

## Extending the System

### Adding New MCP Servers
1. Create new server file in `src/servers/`
2. Implement FastAPI endpoints with `/meta` capability endpoint
3. Add server configuration to `src/config/settings.py`
4. Update event processor logic if needed

### Custom REST API Integration
Use the Custom REST server to integrate any REST API by registering endpoint configurations.