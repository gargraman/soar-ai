
import pytest
from fastapi.testclient import TestClient
from src.servers.servicenow_server import app, records_storage

class TestServiceNowServer:
    """Test cases for ServiceNow MCP Server"""
    
    def setup_method(self):
        """Setup test client and clear storage"""
        self.client = TestClient(app)
        records_storage.clear()
    
    def test_get_metadata(self):
        """Test metadata endpoint"""
        response = self.client.get("/meta")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_name"] == "servicenow"
        assert data["version"] == "1.0.0"
        assert "create_record" in data["capabilities"]
        assert "get_record" in data["capabilities"]
        assert data["authentication_required"] is True
    
    def test_create_record_success(self):
        """Test successful record creation"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {
            "type": "incident",
            "summary": "Test incident",
            "description": "Test description",
            "severity": "high"
        }
        
        response = self.client.post("/create_record", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["type"] == "incident"
        assert data["data"]["summary"] == "Test incident"
        assert data["data"]["severity"] == "high"
        assert data["data"]["status"] == "New"
        assert "record_id" in data["data"]
    
    def test_create_record_no_auth(self):
        """Test record creation without authentication"""
        payload = {
            "type": "incident",
            "summary": "Test incident",
            "description": "Test description"
        }
        
        response = self.client.post("/create_record", json=payload)
        assert response.status_code == 401
    
    def test_get_record_success(self):
        """Test successful record retrieval"""
        headers = {"Authorization": "Bearer test-token"}
        
        # First create a record
        create_payload = {
            "type": "incident",
            "summary": "Test incident",
            "description": "Test description",
            "severity": "medium"
        }
        
        create_response = self.client.post("/create_record", json=create_payload, headers=headers)
        create_data = create_response.json()
        record_id = create_data["data"]["record_id"]
        
        # Now retrieve it
        get_payload = {"record_id": record_id}
        get_response = self.client.post("/get_record", json=get_payload, headers=headers)
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["record_id"] == record_id
        assert get_data["data"]["summary"] == "Test incident"
    
    def test_get_record_not_found(self):
        """Test getting non-existent record"""
        headers = {"Authorization": "Bearer test-token"}
        payload = {"record_id": "NONEXISTENT"}
        
        response = self.client.post("/get_record", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]
    
    def test_get_record_no_auth(self):
        """Test record retrieval without authentication"""
        payload = {"record_id": "TEST123"}
        
        response = self.client.post("/get_record", json=payload)
        assert response.status_code == 401
    
    def test_list_all_records(self):
        """Test listing all records"""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create a few records
        for i in range(3):
            payload = {
                "type": "incident",
                "summary": f"Test incident {i}",
                "description": f"Test description {i}",
                "severity": "low"
            }
            self.client.post("/create_record", json=payload, headers=headers)
        
        # List all records
        response = self.client.get("/records")
        assert response.status_code == 200
        
        data = response.json()
        assert "records" in data
        assert len(data["records"]) == 3
