
# Setup and Configuration Guide

This guide provides step-by-step instructions to configure and use the AI-Driven Agentic Cybersecurity Application with MCP.

## 📋 Prerequisites

- Python 3.11 or higher
- Internet connection for MCP server interactions
- (Optional) Kafka cluster for streaming events

## 🔧 Installation Steps

### 1. Clone and Setup
The application is already set up in your Replit environment. All dependencies are automatically managed.

### 2. Install Dependencies (if running locally)
```bash
pip install -r requirements.txt
```

## 🔐 Authentication Configuration

### Step 1: Configure API Keys
Edit `src/config/settings.py` to add your actual API keys:

```python
# Example configuration
"virustotal": {
    "auth_headers": {
        "X-API-Key": "your-actual-virustotal-api-key"
    }
},
"servicenow": {
    "auth_headers": {
        "Authorization": "Basic base64(username:password)"
    }
},
"cyberreason": {
    "auth_headers": {
        "Authorization": "Bearer your-cyberreason-jwt-token"
    }
}
```

### Step 2: Obtain API Keys

#### VirusTotal API Key
1. Go to https://www.virustotal.com/gui/join-us
2. Create an account or sign in
3. Navigate to your profile → API Key
4. Copy the API key to your configuration

#### ServiceNow Credentials
1. Access your ServiceNow instance
2. Create a service account with incident management permissions
3. Generate basic authentication credentials
4. Encode as base64: `echo -n "username:password" | base64`

#### CyberReason Token
1. Log into your CyberReason console
2. Generate an API token from the administration panel
3. Copy the Bearer token to your configuration

## 🚀 Running the Application

### Option 1: Use Replit Workflows (Recommended)
1. Click "Start MCP Servers" workflow to launch all backend services
2. Wait for all servers to start (about 10-15 seconds)
3. Click "Run Cybersecurity App" to start the desktop application

### Option 2: Manual Launch
```bash
# Start MCP servers
python launch_servers.py

# In another terminal/tab, start the desktop app
python main.py
```

## 📊 Sample Data Usage

The application includes sample security events for testing:

### Using Sample JSON Data
1. In the desktop app, click "Upload JSON/CSV File"
2. Select `sample_data/security_events.json`
3. The events will be loaded and displayed

### Using Sample CSV Data
1. Click "Upload JSON/CSV File"
2. Select `sample_data/security_events.csv`
3. Events will be parsed and made available for analysis

## 🔍 Event Analysis Examples

### Example 1: IP Reputation Check
```
Event: {
  "event_type": "network_traffic",
  "src_ip": "192.168.1.100",
  "severity": "medium"
}

User Prompt: "Check if this IP is malicious"

Expected Result: VirusTotal API call with IP reputation data
```

### Example 2: Incident Creation
```
Event: {
  "event_type": "malware_detection",
  "severity": "high",
  "host_info": {"hostname": "workstation-01"}
}

User Prompt: "Create a ServiceNow ticket if threat level is high"

Expected Result: ServiceNow incident created with event details
```

### Example 3: Endpoint Investigation
```
Event: {
  "event_type": "endpoint_alert",
  "host_info": {"hostname": "server-02"},
  "severity": "critical"
}

User Prompt: "Check endpoint status for compromised hosts"

Expected Result: CyberReason API calls for Pylum ID and terminal status
```

## 📡 Kafka Configuration (Optional)

### Step 1: Setup Kafka (if using streaming)
```bash
# Configure Kafka settings in src/config/settings.py
"kafka_config": {
    "bootstrap_servers": ["your-kafka-broker:9092"],
    "security_protocol": "PLAINTEXT",  # or "SASL_SSL" for secure
    "auto_offset_reset": "latest",
    "topic": "security-events"
}
```

### Step 2: Test Kafka Connection
In the desktop app:
1. Go to "Event Processing" tab
2. Click "Start Kafka Consumer"
3. Enter your topic name
4. Monitor for incoming events

## 🔧 Custom REST API Integration

### Step 1: Register Custom API
Use the Custom REST server to integrate any REST API:

```python
# Example: Adding a threat intelligence API
config = {
    "name": "threat_intel_api",
    "base_url": "https://api.threatintel.com",
    "headers": {"Authorization": "Bearer your-token"},
    "endpoints": {
        "ip_lookup": {
            "path": "/v1/ip/{ip}",
            "method": "GET",
            "parameters": {"ip": "string"}
        },
        "domain_lookup": {
            "path": "/v1/domain/{domain}",
            "method": "GET",
            "parameters": {"domain": "string"}
        }
    }
}
```

### Step 2: Configure Custom Server
1. Open `src/servers/custom_rest_server.py`
2. Add your API configuration to the `REGISTERED_APIS` dictionary
3. Restart the Custom REST server

## 🧪 Testing Your Setup

### Test 1: MCP Server Health Check
```bash
# Test each server endpoint
curl http://0.0.0.0:8001/meta  # VirusTotal
curl http://0.0.0.0:8002/meta  # ServiceNow
curl http://0.0.0.0:8003/meta  # CyberReason
curl http://0.0.0.0:8004/meta  # Custom REST
```

### Test 2: API Authentication
```bash
# Test VirusTotal with API key
curl -X POST http://0.0.0.0:8001/ip_report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"ip": "8.8.8.8"}'

# Test ServiceNow with auth
curl -X POST http://0.0.0.0:8002/create_record \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic your-auth-token" \
  -d '{"type": "incident", "summary": "Test", "description": "Test incident"}'
```

### Test 3: Desktop App Functionality
1. Launch the desktop application
2. Upload sample data
3. Try these test prompts:
   - "Check if this IP is malicious"
   - "Create a ticket for high severity events"
   - "Analyze endpoint status for all hosts"

## 🔍 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep :8001
netstat -an | grep :8002
netstat -an | grep :8003
netstat -an | grep :8004
```

#### Authentication Errors
- Verify API keys are correct and active
- Check API rate limits
- Ensure proper base64 encoding for basic auth

#### Desktop App Issues
- Ensure all MCP servers are running before starting the app
- Check server logs for error messages
- Verify network connectivity

### Debug Mode
Enable detailed logging:
```bash
export DEBUG=1
python main.py
```

### Log Locations
- MCP Server logs: Console output when running `launch_servers.py`
- Desktop app logs: Displayed in the app's audit trail
- Error logs: Console output with stack traces

## 📈 Performance Optimization

### For Large Event Volumes
1. Increase Kafka consumer batch size
2. Use async processing for MCP calls
3. Implement caching for frequent API calls

### For Multiple Users
1. Deploy MCP servers on separate containers
2. Use load balancers for high availability
3. Implement request rate limiting

## 🚀 Deployment on Replit

### Production Deployment
1. Configure environment variables in Replit Secrets
2. Use the deployment tab to publish your app
3. Set up custom domains if needed

### Environment Variables
Add these to Replit Secrets:
```
VIRUSTOTAL_API_KEY=your-key
SERVICENOW_AUTH=your-auth-token
CYBERREASON_TOKEN=your-token
KAFKA_BOOTSTRAP_SERVERS=your-kafka-servers
```

## 📝 Best Practices

### Security
- Never hardcode API keys in source code
- Use environment variables or Replit Secrets
- Implement proper authentication for production
- Regular rotate API keys

### Performance
- Cache frequently accessed data
- Use async operations for I/O bound tasks
- Monitor API rate limits
- Implement proper error handling

### Monitoring
- Set up health checks for MCP servers
- Monitor API response times
- Track event processing metrics
- Log all security-related activities

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs and error messages
3. Test individual components separately
4. Use debug mode for detailed information

---

**Note**: This application is designed for educational and demonstration purposes. Ensure you have proper authorization before connecting to production security systems.
