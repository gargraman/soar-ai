
import pytest
from fastapi.testclient import TestClient
from src.servers.virustotal_server import app

class TestVirusTotalServer:
    """Test cases for VirusTotal MCP Server"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_get_metadata(self):
        """Test metadata endpoint"""
        response = self.client.get("/meta")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_name"] == "virustotal"
        assert data["version"] == "1.0.0"
        assert "ip_report" in data["capabilities"]
        assert "domain_report" in data["capabilities"]
        assert data["authentication_required"] is True
    
    def test_ip_report_success(self):
        """Test successful IP report"""
        headers = {"X-API-Key": "test-key"}
        payload = {"ip": "192.168.1.100"}
        
        response = self.client.post("/ip_report", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["ip"] == "192.168.1.100"
        assert data["data"]["reputation"] == "malicious"
        assert data["data"]["threat_score"] == 85
    
    def test_ip_report_no_auth(self):
        """Test IP report without authentication"""
        payload = {"ip": "192.168.1.100"}
        
        response = self.client.post("/ip_report", json=payload)
        assert response.status_code == 401
    
    def test_ip_report_unknown_ip(self):
        """Test IP report for unknown IP"""
        headers = {"X-API-Key": "test-key"}
        payload = {"ip": "10.0.0.1"}
        
        response = self.client.post("/ip_report", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["ip"] == "10.0.0.1"
        assert data["data"]["reputation"] == "clean"
        assert data["data"]["threat_score"] == 10
    
    def test_domain_report_success(self):
        """Test successful domain report"""
        headers = {"X-API-Key": "test-key"}
        payload = {"domain": "malicious-domain.com"}
        
        response = self.client.post("/domain_report", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["domain"] == "malicious-domain.com"
        assert data["data"]["reputation"] == "malicious"
        assert data["data"]["threat_score"] == 92
    
    def test_domain_report_no_auth(self):
        """Test domain report without authentication"""
        payload = {"domain": "example.com"}
        
        response = self.client.post("/domain_report", json=payload)
        assert response.status_code == 401
    
    def test_domain_report_unknown_domain(self):
        """Test domain report for unknown domain"""
        headers = {"X-API-Key": "test-key"}
        payload = {"domain": "unknown-domain.com"}
        
        response = self.client.post("/domain_report", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["domain"] == "unknown-domain.com"
        assert data["data"]["reputation"] == "clean"
        assert data["data"]["threat_score"] == 5
