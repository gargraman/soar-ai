# Trellix Cloud IVX MCP Server

This is a Model Context Protocol (MCP) server that provides integration with Trellix Cloud IVX (FireEye's malware analysis platform) for file and URL analysis capabilities.

## Overview

The Cloud IVX server provides malware analysis and threat intelligence services, including:
- File hash analysis and reputation lookups
- Detailed malware analysis reports
- URL submission for dynamic analysis
- File submission for sandbox analysis

## Features

### 1. Hash Lookup (`lookup_hashes`)
- Analyze file hashes (MD5, SHA1, SHA256) for malware indicators
- Get verdicts, threat names, and confidence scores
- Optional raw JSON response format
- Batch processing support

### 2. Report Retrieval (`get_report`)
- Get detailed malware analysis reports by report ID
- Optional inclusion of full sandbox details and IoCs
- Comprehensive threat intelligence information

### 3. URL Analysis (`analyse_url`)
- Submit URLs for dynamic malware analysis
- Support for up to 5 URLs per request
- Real-time sandbox analysis results

### 4. File Analysis (`analyse_file`)
- Submit files for malware analysis
- Support for both URL references and file UUIDs
- Comprehensive sandbox analysis

## API Endpoints

### Authentication
All endpoints require authentication via `X-API-Key` header:
```
X-API-Key: your-trellix-cloud-ivx-api-key
```

### Server Metadata
```
GET /meta
```
Returns server capabilities and endpoint information.

### Hash Lookup
```
POST /lookup_hashes
Content-Type: application/json
X-API-Key: your-api-key

{
  "hashes": ["5d41402abc4b2a76b9719d911017c592", "098f6bcd4621d373cade4e832627b4f6"],
  "enable_raw_json": false
}
```

### Get Report
```
POST /get_report
Content-Type: application/json
X-API-Key: your-api-key

{
  "report_id": "550e8400-e29b-41d4-a716-446655440001",
  "include_all": true
}
```

### URL Analysis
```
POST /analyse_url
Content-Type: application/json
X-API-Key: your-api-key

{
  "urls": ["http://suspicious-domain.com", "https://malware-site.net"]
}
```

### File Analysis
```
POST /analyse_file
Content-Type: application/json
X-API-Key: your-api-key

{
  "file_ref": "https://example.com/suspicious-file.exe"
}
```

## Configuration

### Server Configuration
The server runs on port **8005** by default. Update `src/config/settings.py` to configure:

```python
"cloud_ivx": {
    "base_url": "http://0.0.0.0:8005",
    "capabilities": ["lookup_hashes", "get_report", "analyse_url", "analyse_file"],
    "auth_headers": {
        "X-API-Key": "your-trellix-cloud-ivx-api-key"
    }
}
```

### Authentication Setup
1. Obtain API key from Trellix Cloud IVX portal
2. Update the `X-API-Key` value in `src/config/settings.py`
3. Ensure the API key has appropriate permissions for malware analysis

## Usage in Event Processing

The Cloud IVX server integrates with the AI-driven event processor for automatic threat analysis:

### Hash Analysis
When security events contain file hashes, the system can automatically:
- Look up hash reputation in Cloud IVX database
- Determine if files are malicious or clean
- Provide detailed threat intelligence

### URL Analysis
For events containing suspicious URLs:
- Submit URLs for dynamic analysis
- Get sandbox execution results
- Identify C2 communications and malicious behavior

### File Analysis
For file-based security events:
- Submit files for comprehensive malware analysis
- Get detailed behavioral analysis
- Identify attack techniques and IoCs

## Example Event Processing

```python
# Security event with file hashes
event = {
    "event_type": "malware_detection",
    "file_hash_md5": "5d41402abc4b2a76b9719d911017c592",
    "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}

# User prompt
prompt = "Analyze these file hashes for malware indicators"

# AI will automatically route to cloud_ivx for hash analysis
```

## Mock Data

The server includes mock data for testing and demonstration:
- Sample malicious and clean file hashes
- Mock analysis reports with sandbox details
- Simulated URL and file analysis responses

### Sample Hashes for Testing
- `5d41402abc4b2a76b9719d911017c592` - Malicious (Trojan.GenKD.12345)
- `098f6bcd4621d373cade4e832627b4f6` - Clean

## Running the Server

### Start Individual Server
```bash
cd src/servers
python cloud_ivx_server.py
```

### Start All Servers
```bash
python launch_servers.py
```

The server will be available at `http://localhost:8005`

## Testing

### Unit Tests
```bash
pytest tests/test_servers/test_cloud_ivx_server.py -v
```

### Manual Testing
```bash
python test_cloud_ivx.py
```

### Integration Testing
Test with sample data:
```bash
# Start the server first
python launch_servers.py

# Then run the desktop app with hash_analysis_events.json
python main.py
```

## Error Handling

The server provides comprehensive error handling:
- **401 Unauthorized**: Missing or invalid API key
- **422 Validation Error**: Invalid input parameters (malformed UUIDs, too many URLs)
- **404 Not Found**: Report ID not found
- **500 Internal Error**: Server processing errors

## Production Deployment

### Security Considerations
1. Use HTTPS in production environments
2. Implement proper API key rotation
3. Configure rate limiting
4. Enable audit logging
5. Use environment variables for sensitive configuration

### Scalability
- The server uses async FastAPI for high performance
- Supports concurrent request processing
- Can be deployed behind load balancers
- Integrates with container orchestration platforms

## API Documentation

When the server is running, automatic API documentation is available at:
- Swagger UI: `http://localhost:8005/docs`
- ReDoc: `http://localhost:8005/redoc`

## Integration with Other MCP Servers

The Cloud IVX server works seamlessly with other MCP servers:
- **VirusTotal**: Compare hash analysis results
- **ServiceNow**: Create incidents for malicious files
- **CyberReason**: Correlate with endpoint detections
- **Custom REST**: Integrate additional threat intelligence sources

## Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure server is running on port 8005
2. **Authentication Failed**: Verify API key configuration
3. **Invalid UUID**: Ensure report IDs are properly formatted UUIDs
4. **Too Many URLs**: Limit URL analysis to 5 URLs per request

### Debug Mode
Run server with debug logging:
```bash
python cloud_ivx_server.py --log-level debug
```

## Contributing

To extend the Cloud IVX server:
1. Add new endpoints in `cloud_ivx_server.py`
2. Update mock data for testing
3. Add corresponding unit tests
4. Update configuration and documentation
5. Test integration with event processor
