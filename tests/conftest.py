
import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
import json
from typing import Dict, Any

# Test data fixtures
@pytest.fixture
def sample_event_data():
    """Sample security event data for testing"""
    return {
        "id": "EVT-001",
        "timestamp": "2024-01-20T10:30:00Z",
        "event_type": "malware_detection",
        "severity": "high",
        "hostname": "workstation-01",
        "src_ip": "192.168.1.100",
        "dst_ip": "malicious-domain.com",
        "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
        "description": "Suspicious file detected on endpoint"
    }

@pytest.fixture
def sample_event_attributes():
    """Sample extracted event attributes"""
    return {
        "event_type": "malware_detection",
        "indicators": {
            "ips": ["192.168.1.100"],
            "domains": ["malicious-domain.com"],
            "md5": ["d41d8cd98f00b204e9800998ecf8427e"]
        },
        "severity": "high",
        "host_info": {"hostname": "workstation-01"},
        "network_info": {"src_ip": "192.168.1.100", "dst_ip": "malicious-domain.com"}
    }

@pytest.fixture
def mock_server_configs():
    """Mock MCP server configurations"""
    return {
        "virustotal": {
            "base_url": "http://localhost:8001",
            "capabilities": ["ip_report", "domain_report"],
            "auth_headers": {"X-API-Key": "test-key"}
        },
        "servicenow": {
            "base_url": "http://localhost:8002", 
            "capabilities": ["create_record", "get_record"],
            "auth_headers": {"Authorization": "Basic test-auth"}
        },
        "cyberreason": {
            "base_url": "http://localhost:8003",
            "capabilities": ["get_pylum_id", "check_terminal_status"],
            "auth_headers": {"Authorization": "Bearer test-token"}
        }
    }

@pytest.fixture
def mock_virustotal_response():
    """Mock VirusTotal API response"""
    return {
        "success": True,
        "data": {
            "ip": "192.168.1.100",
            "reputation": "malicious",
            "threat_score": 85,
            "detections": 15,
            "total_engines": 20
        }
    }

@pytest.fixture
def mock_servicenow_response():
    """Mock ServiceNow API response"""
    return {
        "success": True,
        "data": {
            "record_id": "INC12345678",
            "type": "incident",
            "summary": "Security event detected",
            "status": "New",
            "created_at": "2024-01-20T10:30:00Z"
        }
    }

@pytest.fixture
def mock_cyberreason_response():
    """Mock CyberReason API response"""
    return {
        "success": True,
        "data": {
            "hostname": "workstation-01",
            "pylum_id": "PYL_12345678",
            "status": "compromised",
            "threat_level": "high",
            "is_compromised": True
        }
    }

@pytest.fixture
def mock_bedrock_client():
    """Mock AWS Bedrock client"""
    mock_client = MagicMock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{
            'text': json.dumps({
                "reasoning": "Test analysis",
                "severity_assessment": "high", 
                "flow_strategy": "Sequential analysis",
                "determined_actions": [
                    {
                        "step": 1,
                        "server": "virustotal",
                        "action": "ip_report",
                        "parameters": {"ip": "192.168.1.100"},
                        "priority": "high",
                        "rationale": "Check IP reputation"
                    }
                ],
                "risk_indicators": ["suspicious_ip"],
                "expected_flow_outcomes": ["IP reputation analysis"],
                "recommended_follow_up": "Monitor endpoint"
            })
        }]
    }).encode()
    
    mock_client.invoke_model.return_value = mock_response
    return mock_client

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
