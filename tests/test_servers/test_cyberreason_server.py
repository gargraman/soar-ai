
import pytest
from fastapi.testclient import TestClient
from src.servers.cyberreason_server import app

class TestCyberReasonServer:
    """Test cases for CyberReason MCP Server"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_get_metadata(self):
        """Test metadata endpoint"""
        response = self.client.get("/meta")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_name"] == "cyberreason"
        assert data["version"] == "1.0.0"
        assert "get_pylum_id" in data["capabilities"]
        assert "check_terminal_status" in data["capabilities"]
        assert data["authentication_required"] is True
    
    def test_get_pylum_id_by_hostname(self):
        """Test getting Pylum ID by hostname"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"hostname": "workstation-01"}
        
        response = self.client.post("/get_pylum_id", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hostname"] == "workstation-01"
        assert data["data"]["pylum_id"] == "PYL_12345678"
        assert data["data"]["sensor_id"] == "SEN_87654321"
    
    def test_get_pylum_id_by_sensor_id(self):
        """Test getting Pylum ID by sensor ID"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"sensor_id": "SEN_87654321"}
        
        response = self.client.post("/get_pylum_id", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hostname"] == "workstation-01"
        assert data["data"]["pylum_id"] == "PYL_12345678"
        assert data["data"]["sensor_id"] == "SEN_87654321"
    
    def test_get_pylum_id_not_found(self):
        """Test getting Pylum ID for unknown endpoint"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"hostname": "unknown-host"}
        
        response = self.client.post("/get_pylum_id", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]
    
    def test_get_pylum_id_no_auth(self):
        """Test getting Pylum ID without authentication"""
        payload = {"hostname": "workstation-01"}
        
        response = self.client.post("/get_pylum_id", json=payload)
        assert response.status_code == 401
    
    def test_check_terminal_status_by_hostname(self):
        """Test checking terminal status by hostname"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"hostname": "workstation-01"}
        
        response = self.client.post("/check_terminal_status", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hostname"] == "workstation-01"
        assert data["data"]["status"] == "compromised"
        assert data["data"]["threat_level"] == "high"
        assert data["data"]["is_compromised"] is True
        assert data["data"]["malops_count"] == 1
    
    def test_check_terminal_status_by_pylum_id(self):
        """Test checking terminal status by Pylum ID"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"pylum_id": "PYL_12345678"}
        
        response = self.client.post("/check_terminal_status", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hostname"] == "workstation-01"
        assert data["data"]["pylum_id"] == "PYL_12345678"
        assert data["data"]["status"] == "compromised"
    
    def test_check_terminal_status_clean_endpoint(self):
        """Test checking status of clean endpoint"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"hostname": "server-02"}
        
        response = self.client.post("/check_terminal_status", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hostname"] == "server-02"
        assert data["data"]["status"] == "clean"
        assert data["data"]["threat_level"] == "low"
        assert data["data"]["is_compromised"] is False
        assert data["data"]["malops_count"] == 0
    
    def test_check_terminal_status_not_found(self):
        """Test checking status of unknown endpoint"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"hostname": "unknown-endpoint"}
        
        response = self.client.post("/check_terminal_status", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]
    
    def test_check_terminal_status_no_auth(self):
        """Test checking terminal status without authentication"""
        payload = {"hostname": "workstation-01"}
        
        response = self.client.post("/check_terminal_status", json=payload)
        assert response.status_code == 401
