
# AI-Driven Agentic Cybersecurity Application with MCP

A comprehensive cybersecurity application that uses the Model Context Protocol (MCP) to create an AI-driven agent system for security event analysis, enrichment, and response.

## 🚀 Features

### MCP Client (Desktop App)
- **Multi-source Event Input**: Upload JSON/CSV files or stream from Kafka topics
- **Natural Language Processing**: Accept user prompts in plain English
- **AI-Powered Decision Making**: Automatically determine which MCP servers to query
- **Interactive Results Display**: View enrichment data, analysis results, and response actions
- **Comprehensive Audit Trail**: Track all agent decisions and API calls

### Supported MCP Servers
1. **VirusTotal Server** - IP and domain reputation lookup
2. **ServiceNow Server** - Incident and task management
3. **CyberReason Server** - Endpoint status and threat detection
4. **Custom REST Server** - Generic REST API wrapper with OpenAPI support

### Event Types Supported
- IP/domain/file-based Indicators of Compromise (IOCs)
- Host telemetry and endpoint events  
- Detection rule matches from SIEM systems
- Network anomalies and traffic analysis
- Authentication and access events

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop App   │────│  Event Processor │────│   MCP Client    │
│   (Tkinter GUI) │    │  (AI Reasoning)  │    │ (HTTP Requests) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ File/   │              │ Prompt  │              │  MCP    │
    │ Kafka   │              │ Analysis│              │ Servers │
    │ Input   │              │ Engine  │              │         │
    └─────────┘              └─────────┘              └─────────┘
                                                           │
                        ┌──────────────────────────────────┼────────────────┐
                        │                                  │                │
                  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
                  │VirusTotal │  │ServiceNow │  │CyberReason│  │Custom REST│
                  │  Server   │  │  Server   │  │  Server   │  │  Server   │
                  │  :8001    │  │  :8002    │  │  :8003    │  │  :8004    │
                  └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

## 🚦 Quick Start

### 1. Launch MCP Servers
```bash
python launch_servers.py
```

This will start all four MCP servers:
- VirusTotal Server: http://0.0.0.0:8001
- ServiceNow Server: http://0.0.0.0:8002  
- CyberReason Server: http://0.0.0.0:8003
- Custom REST Server: http://0.0.0.0:8004

### 2. Run the Desktop Application
```bash
python main.py
```

### 3. Upload Sample Data
Use the provided sample files:
- `sample_data/security_events.json` - Comprehensive security events
- `sample_data/security_events.csv` - Additional events in CSV format

### 4. Try Example Prompts
- "Check if this IP is malicious and create a high-priority ServiceNow ticket if threat level is critical"
- "Analyze these network events for indicators of compromise"
- "Get endpoint status from CyberReason for any compromised hosts"
- "Enrich all IOCs and create incident reports for high-severity events"

## 🎯 Usage Examples

### Example 1: Malware Analysis
```
Prompt: "Check if this IP is malicious"
Event: Contains IP 192.168.1.100

Agent Decision:
1. Query VirusTotal for IP reputation
2. Return threat intelligence data

Result: IP flagged as malicious with 85% threat score
```

### Example 2: Incident Creation
```
Prompt: "Create a ServiceNow ticket if threat level is high"
Event: High-severity malware detection

Agent Decision:
1. Analyze event severity (high)
2. Create ServiceNow incident record
3. Return incident ID and details

Result: Incident INC12345678 created successfully
```

### Example 3: Endpoint Investigation
```
Prompt: "Check endpoint status for compromised hosts"
Event: Contains hostname "workstation-01"

Agent Decision:
1. Query CyberReason for Pylum ID
2. Check terminal compromise status
3. Return detailed endpoint analysis

Result: Host confirmed compromised with active malware
```

## 🔧 Configuration

### MCP Server Configuration
Edit `src/config/settings.py` to customize:

```python
mcp_servers = {
    "virustotal": {
        "base_url": "http://0.0.0.0:8001",
        "auth_headers": {"X-API-Key": "your-api-key"}
    },
    "servicenow": {
        "base_url": "http://0.0.0.0:8002", 
        "auth_headers": {"Authorization": "Basic your-auth"}
    }
    # ... additional servers
}
```

### Authentication Setup
Each MCP server supports authentication:

1. **VirusTotal**: Requires `X-API-Key` header
2. **ServiceNow**: Requires `Authorization` header (Basic/Bearer)
3. **CyberReason**: Requires `Authorization` Bearer token
4. **Custom REST**: Configurable per API

## 🧪 API Testing

Test individual MCP servers using curl:

```bash
# Test VirusTotal server
curl -X POST http://0.0.0.0:8001/ip_report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"ip": "192.168.1.100"}'

# Test ServiceNow server
curl -X POST http://0.0.0.0:8002/create_record \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic test-auth" \
  -d '{"type": "incident", "summary": "Test incident", "description": "Test description"}'

# Get server capabilities
curl http://0.0.0.0:8001/meta
```

## 🔍 Event Routing Logic

The AI agent analyzes events and prompts using these decision factors:

### Event Attributes
- **IOCs**: IPs, domains, file hashes
- **Host Information**: Hostnames, endpoints
- **Severity Levels**: Critical, high, medium, low
- **Event Types**: Malware, network anomaly, failed logins

### Prompt Analysis
- **Keywords**: "malicious", "ticket", "endpoint", "reputation"
- **Actions**: "check", "create", "analyze", "investigate"
- **Conditions**: "if high severity", "if compromised"

### Fallback Logic
If no specific servers are mentioned:
1. Default to VirusTotal for IOC enrichment
2. Create ServiceNow tickets for high/critical severity
3. Check CyberReason for any host-related events

## 📊 Audit Trail

The application maintains comprehensive logging:

```json
{
  "event_id": "evt_001",
  "timestamp": "2024-01-20T10:30:00Z",
  "user_prompt": "Check if this IP is malicious",
  "analysis": {
    "event_attributes": {...},
    "determined_actions": [...],
    "reasoning": "..."
  },
  "results": [
    {
      "action": {...},
      "success": true,
      "result": {...}
    }
  ]
}
```

## 🔌 Extending the System

### Adding New MCP Servers
1. Create new server file in `src/servers/`
2. Implement FastAPI endpoints with `/meta` capability
3. Add server configuration to `settings.py`
4. Update event processor logic if needed

### Custom REST API Integration
Use the Custom REST server to integrate any REST API:

```python
# Register new API
config = {
    "name": "custom_threat_intel",
    "base_url": "https://api.threatintel.com",
    "headers": {"Authorization": "Bearer token"},
    "endpoints": {
        "ip_lookup": {
            "path": "/v1/ip/{ip}",
            "method": "GET"
        }
    }
}
```

## 🛠️ Development

### Project Structure
```
src/
├── client/          # Desktop application and MCP client
├── servers/         # MCP server implementations
├── config/          # Configuration management
sample_data/         # Sample security events
launch_servers.py    # Server launcher utility
main.py             # Application entry point
```

### Running in Development
1. Install dependencies: `pip install -r requirements.txt`
2. Start servers: `python launch_servers.py`
3. Run application: `python main.py`

## 📝 License

This project is designed for educational and demonstration purposes. Ensure you have proper authorization before connecting to production security systems.

## 🆘 Troubleshooting

### Common Issues
1. **Port conflicts**: Change ports in server files if 8001-8004 are occupied
2. **Import errors**: Ensure all dependencies are installed
3. **Server connection**: Verify servers are running before starting the desktop app
4. **Authentication**: Check API keys and tokens in configuration

### Debug Mode
Set environment variable for detailed logging:
```bash
export DEBUG=1
python main.py
```
