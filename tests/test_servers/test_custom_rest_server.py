
import pytest
from fastapi.testclient import TestClient
from src.servers.custom_rest_server import app, registered_apis

class TestCustomRestServer:
    """Test cases for Custom REST MCP Server"""
    
    def setup_method(self):
        """Setup test client and clear registered APIs"""
        self.client = TestClient(app)
        registered_apis.clear()
    
    def test_get_metadata(self):
        """Test metadata endpoint"""
        response = self.client.get("/meta")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_name"] == "custom_rest"
        assert data["version"] == "1.0.0"
        assert "register_api" in data["capabilities"]
        assert "call_endpoint" in data["capabilities"]
        assert "list_apis" in data["capabilities"]
        assert data["authentication_required"] is False
    
    def test_register_api_success(self):
        """Test successful API registration"""
        payload = {
            "config": {
                "name": "test_api",
                "base_url": "https://api.example.com",
                "headers": {"Authorization": "Bearer token"},
                "endpoints": {
                    "get_users": {
                        "path": "/users",
                        "method": "GET",
                        "description": "Get all users"
                    },
                    "create_user": {
                        "path": "/users",
                        "method": "POST",
                        "description": "Create a user"
                    }
                }
            }
        }
        
        response = self.client.post("/register_api", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "test_api" in data["data"]["message"]
        assert "get_users" in data["data"]["endpoints"]
        assert "create_user" in data["data"]["endpoints"]
    
    def test_list_apis_empty(self):
        """Test listing APIs when none are registered"""
        response = self.client.get("/list_apis")
        assert response.status_code == 200
        
        data = response.json()
        assert "registered_apis" in data
        assert len(data["registered_apis"]) == 0
    
    def test_list_apis_with_registered_api(self):
        """Test listing APIs after registration"""
        # First register an API
        payload = {
            "config": {
                "name": "test_api",
                "base_url": "https://api.example.com",
                "headers": {},
                "endpoints": {
                    "test_endpoint": {
                        "path": "/test",
                        "method": "GET"
                    }
                }
            }
        }
        
        self.client.post("/register_api", json=payload)
        
        # Now list APIs
        response = self.client.get("/list_apis")
        assert response.status_code == 200
        
        data = response.json()
        assert "registered_apis" in data
        assert "test_api" in data["registered_apis"]
        assert data["registered_apis"]["test_api"]["base_url"] == "https://api.example.com"
        assert "test_endpoint" in data["registered_apis"]["test_api"]["endpoints"]
    
    @pytest.mark.skip(reason="Requires external HTTP mocking")
    def test_call_endpoint_success(self):
        """Test successful endpoint call (would require HTTP mocking)"""
        # This test would require mocking external HTTP calls
        # Skipping for now as it requires additional setup
        pass
    
    def test_call_endpoint_api_not_registered(self):
        """Test calling endpoint on unregistered API"""
        payload = {
            "api_name": "unknown_api",
            "endpoint_name": "test_endpoint",
            "parameters": {}
        }
        
        response = self.client.post("/call_endpoint", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not registered" in data["error"]
    
    def test_call_endpoint_endpoint_not_found(self):
        """Test calling unknown endpoint on registered API"""
        # First register an API
        register_payload = {
            "config": {
                "name": "test_api",
                "base_url": "https://api.example.com",
                "headers": {},
                "endpoints": {
                    "known_endpoint": {
                        "path": "/known",
                        "method": "GET"
                    }
                }
            }
        }
        
        self.client.post("/register_api", json=register_payload)
        
        # Try to call unknown endpoint
        call_payload = {
            "api_name": "test_api",
            "endpoint_name": "unknown_endpoint",
            "parameters": {}
        }
        
        response = self.client.post("/call_endpoint", json=call_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]
    
    def test_register_from_openapi(self):
        """Test registering API from OpenAPI specification"""
        openapi_spec = {
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "Get all users",
                        "parameters": []
                    },
                    "post": {
                        "operationId": "createUser", 
                        "summary": "Create a user",
                        "parameters": []
                    }
                }
            }
        }
        
        response = self.client.post("/register_from_openapi", 
                                  json=openapi_spec, 
                                  params={"api_name": "openapi_test"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "openapi_test" in data["data"]["message"]
        assert "getUsers" in data["data"]["endpoints"]
        assert "createUser" in data["data"]["endpoints"]
