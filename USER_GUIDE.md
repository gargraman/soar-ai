# User Guide - AI Cybersecurity Agent

Complete guide for using the AI-Driven Agentic Cybersecurity Application with MCP.

## 🚀 Getting Started

### Quick Start Checklist
- [ ] Configure API keys in `src/config/settings.py`
- [ ] Start MCP servers using "Start MCP Servers" workflow
- [ ] Launch desktop app using "Run Cybersecurity App" workflow
- [ ] Upload sample data to test functionality
- [ ] Try example prompts to understand AI capabilities

## 🖥️ Desktop Application Interface

### Main Window Overview
The desktop application consists of four main tabs:

1. **Event Processing** - Upload files and process events
2. **Results** - View analysis results and responses
3. **Audit Trail** - Track all actions and decisions
4. **Configuration** - Manage server settings

### Event Processing Tab

#### File Upload Section
- **Purpose**: Upload JSON or CSV files containing security events
- **Supported Formats**: 
  - JSON: Structured security event data
  - CSV: Comma-separated security event data
- **Sample Files**: Use provided files in `sample_data/` folder

#### Kafka Consumer Section
- **Purpose**: Stream real-time security events from Kafka topics
- **Configuration**: Enter Kafka topic name and connection details
- **Status**: Monitor connection status and message count

#### Event Analysis Section
- **Event Display**: Shows loaded events in structured format
- **Prompt Input**: Enter natural language instructions for the AI agent
- **Process Button**: Execute AI analysis and response actions

### Results Tab

#### Analysis Results
- **Event Summary**: Overview of processed events
- **Action Decisions**: AI agent's decision-making process
- **Server Responses**: Results from MCP server queries
- **Success/Failure Status**: Outcome of each action

#### Response Data
- **Enrichment Data**: IOC analysis results from VirusTotal
- **Ticket Information**: ServiceNow incident details
- **Endpoint Status**: CyberReason host analysis
- **Custom API Results**: Additional enrichment data

### Audit Trail Tab

#### Activity Log
- **Event Timeline**: Chronological list of all activities
- **Decision Records**: AI agent reasoning for each action
- **API Call History**: Complete log of MCP server interactions
- **Export Options**: Download audit logs in various formats

#### Filtering Options
- **Date Range**: Filter activities by time period
- **Event Types**: Filter by specific event categories
- **Server Actions**: Filter by MCP server interactions
- **Success/Failure**: Filter by action outcomes

### Configuration Tab

#### Server Management
- **Server Status**: Monitor health of all MCP servers
- **Connection Testing**: Test connectivity to each server
- **Configuration Updates**: Modify server settings without restart
- **API Key Management**: Securely update authentication tokens

## 🔍 Event Types and Processing

### Supported Event Types

#### Network Events
```json
{
  "event_type": "network_traffic",
  "timestamp": "2024-01-20T10:30:00Z",
  "src_ip": "192.168.1.100",
  "dst_ip": "8.8.8.8",
  "protocol": "TCP",
  "port": 80,
  "severity": "medium"
}
```

#### Malware Detection
```json
{
  "event_type": "malware_detection",
  "timestamp": "2024-01-20T10:25:00Z",
  "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
  "file_name": "suspicious.exe",
  "host_info": {
    "hostname": "workstation-01",
    "ip_address": "192.168.1.100"
  },
  "severity": "high"
}
```

#### Authentication Events
```json
{
  "event_type": "failed_login",
  "timestamp": "2024-01-20T10:20:00Z",
  "username": "admin",
  "source_ip": "192.168.1.150",
  "attempts": 5,
  "severity": "medium"
}
```

#### Endpoint Alerts
```json
{
  "event_type": "endpoint_alert",
  "timestamp": "2024-01-20T10:35:00Z",
  "host_info": {
    "hostname": "server-02",
    "os": "Windows Server 2019",
    "ip_address": "192.168.1.50"
  },
  "alert_type": "process_anomaly",
  "severity": "high"
}
```

### Event Processing Workflow

1. **Event Ingestion**: Upload file or consume from Kafka
2. **Data Parsing**: Extract relevant fields and attributes
3. **Prompt Analysis**: AI agent analyzes user instructions
4. **Action Determination**: Decide which MCP servers to query
5. **Execution**: Make API calls to relevant servers
6. **Response Processing**: Aggregate and format results
7. **Audit Logging**: Record all activities and decisions

## 🤖 AI Agent Capabilities

### Natural Language Processing

#### Supported Prompt Types

**IOC Analysis**
- "Check if this IP is malicious"
- "Analyze these domains for reputation"
- "Lookup file hash in threat intelligence"
- "Enrich all IOCs in the event"

**Incident Management**
- "Create a ServiceNow ticket for high severity events"
- "Generate incident report if threat level is critical"
- "Create ticket with priority based on severity"
- "Update existing incident with new information"

**Endpoint Investigation**
- "Check endpoint status for compromised hosts"
- "Get Pylum ID for all hostnames"
- "Investigate terminal compromise status"
- "Analyze endpoint for active threats"

#### Complex Analysis
- "Analyze network events for indicators of compromise"
- "Investigate authentication failures and create tickets if needed"
- "Enrich all IOCs and create incident for high-severity events"
- "Full investigation workflow for malware detection"

#### Sequential Flow Orchestration
- "First check IP reputation, then create ticket if malicious, finally investigate endpoint status"
- "Enrich all IOCs via VirusTotal, then create ServiceNow incident with threat intelligence, then check all endpoints via CyberReason"
- "Analyze file hash for malware, if confirmed malicious create critical incident and check affected endpoints"
- "Investigate authentication anomalies step by step: check source IP reputation, create incident if threats found, then analyze endpoint security"

#### Conditional Logic Flows
- "Check IP reputation, if threat score > 80 create critical incident and investigate all related endpoints"
- "Analyze domain reputation, create incident only if malicious detections > 5, then update incident with endpoint findings"
- "For each suspicious file hash: analyze via VirusTotal, if malicious create incident, then check host status and update incident accordingly"
- "Sequential threat hunt: check all IOCs, create incidents for high-risk findings, investigate endpoints for confirmed threats"

#### Multi-Stage Investigation Workflows
- "Complete security incident response: analyze all IOCs, create incident with findings, investigate affected systems, update incident with remediation status"
- "Advanced threat hunting: enrich network indicators, correlate with endpoint data, create comprehensive incident report with full timeline"
- "Malware outbreak investigation: analyze file signatures, check reputation across all security feeds, create incident, map affected endpoints, coordinate response"

### Decision-Making Logic

#### Keyword Analysis
The AI agent analyzes prompts for specific keywords:

- **Malicious/Reputation**: Triggers VirusTotal queries
- **Ticket/Incident**: Triggers ServiceNow actions
- **Endpoint/Terminal**: Triggers CyberReason queries
- **Investigate/Analyze**: Triggers comprehensive analysis
- **Enrich/Lookup**: Triggers multiple enrichment sources

#### Severity-Based Actions
- **Critical/High**: Full analysis with incident creation
- **Medium**: IOC enrichment and monitoring
- **Low**: Basic enrichment only

#### Contextual Decisions
- **IP Addresses**: Automatic VirusTotal IP reputation check
- **Domains**: Automatic VirusTotal domain analysis
- **File Hashes**: Automatic malware analysis
- **Hostnames**: Automatic CyberReason endpoint check

## 📊 Working with Results

### Understanding Output Format

#### VirusTotal Results
```json
{
  "ip": "192.168.1.100",
  "reputation": "malicious",
  "threat_score": 85,
  "detections": {
    "malicious": 12,
    "suspicious": 5,
    "clean": 3
  },
  "last_analysis_date": "2024-01-20T10:30:00Z"
}
```

#### ServiceNow Results
```json
{
  "incident_id": "INC12345678",
  "number": "INC0000123",
  "state": "New",
  "priority": "2 - High",
  "short_description": "Security event detected",
  "created_by": "security_agent",
  "created_on": "2024-01-20T10:30:00Z"
}
```

#### CyberReason Results
```json
{
  "hostname": "workstation-01",
  "pylum_id": "PYL_12345678",
  "status": "compromised",
  "threat_level": "high",
  "malops": [
    {
      "malop_id": "MALOP_001",
      "type": "malware",
      "severity": "high"
    }
  ]
}
```

### Interpreting Results

#### Threat Scores
- **90-100**: Critical threat, immediate action required
- **70-89**: High threat, investigation recommended
- **50-69**: Medium threat, monitoring advised
- **0-49**: Low threat, informational only

#### Status Indicators
- **✅ Success**: Action completed successfully
- **❌ Error**: Action failed, check logs for details
- **⏳ Pending**: Action in progress
- **⚠️ Warning**: Action completed with warnings

## 🔄 Advanced Usage

### Batch Processing

#### Processing Multiple Events
1. Upload file with multiple events
2. Use prompts like "Analyze all events for threats"
3. AI agent will process each event individually
4. Results are aggregated and presented together

#### Streaming Processing
1. Configure Kafka consumer with topic name
2. Start streaming with "Start Kafka Consumer"
3. Events are processed in real-time as they arrive
4. Results are displayed continuously

### Custom Workflows

#### Creating Custom Analysis Workflows
```
Prompt: "For each malware event, check IP reputation, create high-priority ticket, and investigate endpoint status"

AI Agent Actions:
1. Identify malware events
2. Extract IP addresses → VirusTotal
3. Create ServiceNow incidents with high priority
4. Extract hostnames → CyberReason investigation
5. Aggregate results and provide summary
```

#### Conditional Logic
```
Prompt: "If threat score > 80, create critical incident and check all related endpoints"

AI Agent Logic:
1. Analyze threat scores from enrichment
2. For high scores: Create critical ServiceNow incident
3. For high scores: Check all hostnames via CyberReason
4. For low scores: Log for monitoring only
```

### Integration with External Systems

#### Kafka Integration
1. Configure Kafka connection in settings
2. Use appropriate security protocols (PLAINTEXT/SASL_SSL)
3. Monitor consumer lag and message processing rates
4. Handle connection failures gracefully

#### API Integration
1. Use Custom REST server for additional APIs
2. Configure authentication for each API
3. Map response fields to standard format
4. Handle rate limiting and timeouts

## 🛠️ Troubleshooting Guide

### Common Issues and Solutions

#### Authentication Errors
**Problem**: API calls failing with 401/403 errors
**Solution**: 
- Verify API keys are correct and active
- Check token expiration dates
- Ensure proper header formatting
- Test authentication with curl commands

#### Connection Timeouts
**Problem**: Requests timing out or failing
**Solution**:
- Check network connectivity
- Verify server URLs and ports
- Increase timeout values in configuration
- Monitor server resource usage

#### Event Processing Errors
**Problem**: Events not being processed correctly
**Solution**:
- Validate event format and structure
- Check for required fields
- Review AI agent decision logic
- Enable debug logging for detailed information

#### Server Startup Issues
**Problem**: MCP servers failing to start
**Solution**:
- Check port availability
- Verify Python dependencies
- Review server logs for errors
- Ensure proper file permissions

### Debug Mode

Enable debug logging for troubleshooting:
```bash
export DEBUG=1
python main.py
```

Debug mode provides:
- Detailed request/response logs
- AI agent decision reasoning
- Server communication details
- Performance metrics

### Performance Optimization

#### For Large Data Volumes
- Increase batch processing size
- Use async processing where possible
- Implement caching for frequent queries
- Monitor memory usage

#### For Network Issues
- Increase timeout values
- Implement retry mechanisms
- Use connection pooling
- Monitor API rate limits

## 📝 Best Practices

### Security
- Keep API keys secure and rotated regularly
- Use environment variables for sensitive data
- Monitor API usage and limits
- Implement proper access controls

### Performance
- Process events in batches when possible
- Use caching for repeated queries
- Monitor resource usage
- Implement proper error handling

### Monitoring
- Review audit logs regularly
- Monitor API response times
- Track error rates and patterns
- Set up alerts for critical issues

### Data Management
- Backup important configurations
- Archive old audit logs
- Monitor disk space usage
- Implement data retention policies

---

This user guide provides comprehensive instructions for effectively using the AI-Driven Agentic Cybersecurity Application. For additional help, refer to the troubleshooting section or review the configuration documentation.