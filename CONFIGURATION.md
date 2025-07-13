
# Configuration Reference

Complete configuration options for the AI-Driven Agentic Cybersecurity Application.

## 🔧 Main Configuration File

The primary configuration is located in `src/config/settings.py`. Here's the complete structure:

```python
class AppConfig:
    def __init__(self):
        self.mcp_servers = {
            # MCP Server configurations
        }
        self.kafka_config = {
            # Kafka streaming configuration
        }
        self.ui_config = {
            # Desktop app UI settings
        }
        self.security_config = {
            # Security and authentication settings
        }
```

## 🌐 MCP Server Configuration

### VirusTotal Server
```python
"virustotal": {
    "base_url": "http://0.0.0.0:8001",
    "capabilities": ["ip_report", "domain_report"],
    "auth_headers": {
        "X-API-Key": "your-virustotal-api-key"
    },
    "timeout": 30,
    "rate_limit": {
        "requests_per_minute": 4,  # Free tier limit
        "burst_limit": 1
    },
    "endpoints": {
        "ip_report": "/ip_report",
        "domain_report": "/domain_report"
    }
}
```

### ServiceNow Server
```python
"servicenow": {
    "base_url": "http://0.0.0.0:8002",
    "capabilities": ["create_record", "get_record", "update_record"],
    "auth_headers": {
        "Authorization": "Basic base64(username:password)"
        # Alternative: "Authorization": "Bearer jwt-token"
    },
    "timeout": 45,
    "instance_url": "https://your-instance.service-now.com",
    "table_configs": {
        "incident": {
            "table": "incident",
            "required_fields": ["short_description", "description"],
            "default_values": {
                "category": "security",
                "subcategory": "threat_detection",
                "priority": "2"
            }
        }
    }
}
```

### CyberReason Server
```python
"cyberreason": {
    "base_url": "http://0.0.0.0:8003",
    "capabilities": ["get_pylum_id", "check_terminal_status", "get_malops"],
    "auth_headers": {
        "Authorization": "Bearer your-cyberreason-jwt-token"
    },
    "timeout": 60,
    "server_url": "https://your-cyberreason-server.com",
    "api_version": "v1",
    "endpoints": {
        "pylum_lookup": "/pylums/lookup",
        "terminal_status": "/terminals/status",
        "malops": "/malops"
    }
}
```

### Custom REST Server
```python
"custom_rest": {
    "base_url": "http://0.0.0.0:8004",
    "capabilities": ["custom_enrichment", "dynamic_api_calls"],
    "auth_headers": {},
    "timeout": 30,
    "registered_apis": {
        "threat_intel": {
            "base_url": "https://api.threatintel.com",
            "auth_header": "X-API-Key",
            "endpoints": {
                "ip_lookup": "/v1/ip/{ip}",
                "domain_lookup": "/v1/domain/{domain}"
            }
        },
        "osint_feeds": {
            "base_url": "https://feeds.osint.com",
            "auth_header": "Authorization",
            "endpoints": {
                "ioc_search": "/v2/search/ioc",
                "feed_updates": "/v2/feeds/latest"
            }
        }
    }
}
```

## 📡 Kafka Configuration

### Basic Kafka Setup
```python
"kafka_config": {
    "bootstrap_servers": ["localhost:9092"],
    "security_protocol": "PLAINTEXT",
    "auto_offset_reset": "latest",
    "enable_auto_commit": True,
    "auto_commit_interval_ms": 1000,
    "session_timeout_ms": 30000,
    "heartbeat_interval_ms": 10000,
    "max_poll_records": 500,
    "consumer_timeout_ms": 10000
}
```

### Secure Kafka (SASL/SSL)
```python
"kafka_config": {
    "bootstrap_servers": ["kafka-broker:9093"],
    "security_protocol": "SASL_SSL",
    "sasl_mechanism": "PLAIN",
    "sasl_plain_username": "your-username",
    "sasl_plain_password": "your-password",
    "ssl_check_hostname": True,
    "ssl_ca_location": "/path/to/ca-cert.pem",
    "auto_offset_reset": "latest"
}
```

## 🖥️ Desktop App Configuration

### UI Settings
```python
"ui_config": {
    "window_size": "1200x800",
    "theme": "default",  # or "dark"
    "font_family": "Arial",
    "font_size": 10,
    "auto_refresh_interval": 5000,  # milliseconds
    "max_audit_logs": 1000,
    "default_file_path": "./sample_data/",
    "export_formats": ["json", "csv", "pdf"]
}
```

### Event Processing Settings
```python
"event_processing": {
    "max_concurrent_requests": 5,
    "request_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,  # seconds
    "batch_size": 10,
    "enable_caching": True,
    "cache_ttl": 300  # seconds
}
```

## 🔐 Security Configuration

### Authentication Settings
```python
"security_config": {
    "api_key_validation": True,
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 60,
        "burst_limit": 10
    },
    "ssl_verification": True,
    "timeout_settings": {
        "connect_timeout": 10,
        "read_timeout": 30
    },
    "allowed_hosts": ["0.0.0.0", "localhost", "127.0.0.1"],
    "cors_settings": {
        "allow_origins": ["*"],
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["*"]
    }
}
```

## 🔄 Event Type Mappings

### IOC Processing Configuration
```python
"ioc_processing": {
    "ip_patterns": [
        r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    ],
    "domain_patterns": [
        r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
    ],
    "hash_patterns": {
        "md5": r"^[a-fA-F0-9]{32}$",
        "sha1": r"^[a-fA-F0-9]{40}$",
        "sha256": r"^[a-fA-F0-9]{64}$"
    },
    "auto_enrichment": {
        "enabled": True,
        "providers": ["virustotal", "custom_rest"],
        "threshold_score": 0.7
    }
}
```

## 🤖 AI Agent Configuration

### Prompt Analysis Settings
```python
"ai_agent": {
    "analysis_model": "rule_based",  # Future: "llm_based"
    "confidence_threshold": 0.8,
    "max_actions_per_event": 5,
    "action_prioritization": {
        "high_severity": ["servicenow", "cyberreason", "virustotal"],
        "medium_severity": ["virustotal", "custom_rest"],
        "low_severity": ["virustotal"]
    },
    "keyword_mappings": {
        "malicious": ["virustotal"],
        "ticket": ["servicenow"],
        "endpoint": ["cyberreason"],
        "investigate": ["virustotal", "cyberreason"],
        "enrich": ["virustotal", "custom_rest"]
    }
}
```

## 📊 Logging Configuration

### Audit Trail Settings
```python
"logging_config": {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_logging": {
        "enabled": True,
        "file_path": "./logs/app.log",
        "max_size": "10MB",
        "backup_count": 5
    },
    "audit_logging": {
        "enabled": True,
        "file_path": "./logs/audit.log",
        "include_request_body": True,
        "include_response_body": False
    }
}
```

## 🔧 Environment Variables

### Required Environment Variables
```bash
# API Keys
VIRUSTOTAL_API_KEY=your-virustotal-api-key
SERVICENOW_USERNAME=your-servicenow-username
SERVICENOW_PASSWORD=your-servicenow-password
CYBERREASON_TOKEN=your-cyberreason-jwt-token

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
KAFKA_TOPIC=security-events

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
MAX_WORKERS=5
```

### Optional Environment Variables
```bash
# Custom REST APIs
CUSTOM_API_1_URL=https://api.example.com
CUSTOM_API_1_KEY=your-api-key

# Advanced Settings
ENABLE_CACHING=True
CACHE_TTL=300
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
```

## 🌐 Server Port Configuration

### Default Port Assignments
```python
"server_ports": {
    "virustotal": 8001,
    "servicenow": 8002,
    "cyberreason": 8003,
    "custom_rest": 8004,
    "health_check": 8005
}
```

### Custom Port Configuration
To change server ports, modify the respective server files:

1. **VirusTotal Server**: Edit `src/servers/virustotal_server.py`
2. **ServiceNow Server**: Edit `src/servers/servicenow_server.py`
3. **CyberReason Server**: Edit `src/servers/cyberreason_server.py`
4. **Custom REST Server**: Edit `src/servers/custom_rest_server.py`

## 🔄 Configuration Loading

### Loading Configuration from File
```python
# Load from JSON file
config = AppConfig.load_from_file("config.json")

# Load from environment variables
config = AppConfig.load_from_env()

# Load with custom overrides
config = AppConfig.load_with_overrides({
    "mcp_servers": {
        "virustotal": {
            "timeout": 60
        }
    }
})
```

### Configuration Validation
```python
def validate_configuration(config):
    """Validate configuration settings"""
    required_fields = [
        "mcp_servers",
        "kafka_config",
        "ui_config"
    ]
    
    for field in required_fields:
        if not hasattr(config, field):
            raise ValueError(f"Missing required configuration: {field}")
    
    # Validate API keys
    for server_name, server_config in config.mcp_servers.items():
        if server_config.get("auth_headers"):
            print(f"✓ {server_name} authentication configured")
        else:
            print(f"⚠ {server_name} authentication not configured")
```

## 📝 Configuration Best Practices

### 1. Security
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use least privilege access principles

### 2. Performance
- Adjust timeout values based on network conditions
- Configure appropriate rate limits
- Use caching for frequently accessed data
- Monitor resource usage

### 3. Monitoring
- Enable comprehensive logging
- Set up health checks for all services
- Monitor API response times
- Track error rates and patterns

### 4. Scalability
- Use connection pooling for high-volume scenarios
- Implement circuit breakers for external APIs
- Configure proper retry mechanisms
- Monitor resource utilization

---

This configuration reference provides comprehensive settings for all components of the cybersecurity application. Adjust values based on your specific environment and requirements.
