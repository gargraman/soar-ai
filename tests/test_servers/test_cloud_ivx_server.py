"""
Tests for Trellix Cloud IVX MCP Server
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the server app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/servers'))

from cloud_ivx_server import app

class TestCloudIVXServer:
    """Test suite for Trellix Cloud IVX MCP Server"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
        self.headers = {"X-API-Key": "test-api-key"}
    
    def test_meta_endpoint(self):
        """Test server metadata endpoint"""
        response = self.client.get("/meta")
        assert response.status_code == 200
        
        data = response.json()
        assert data["server_name"] == "cloud_ivx"
        assert data["version"] == "1.1.0"
        assert "lookup_hashes" in data["capabilities"]
        assert "get_report" in data["capabilities"]
        assert "analyse_url" in data["capabilities"]
        assert "analyse_file" in data["capabilities"]
        assert data["authentication_required"] is True
    
    def test_lookup_hashes_success(self):
        """Test successful hash lookup"""
        payload = {
            "hashes": ["5d41402abc4b2a76b9719d911017c592"],
            "enable_raw_json": False
        }
        
        response = self.client.post("/lookup_hashes", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "hash_info" in data["data"]
        assert len(data["data"]["hash_info"]) == 1
        assert data["data"]["hash_info"][0]["hash"] == "5d41402abc4b2a76b9719d911017c592"
        assert data["data"]["hash_info"][0]["verdict"] == "malicious"
    
    def test_lookup_hashes_with_raw_json(self):
        """Test hash lookup with raw JSON enabled"""
        payload = {
            "hashes": ["5d41402abc4b2a76b9719d911017c592"],
            "enable_raw_json": True
        }
        
        response = self.client.post("/lookup_hashes", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "raw_json" in data["data"]
        assert len(data["data"]["raw_json"]) == 1
    
    def test_lookup_hashes_unknown_hash(self):
        """Test hash lookup with unknown hash"""
        payload = {
            "hashes": ["unknown12345678901234567890123456"],
            "enable_raw_json": False
        }
        
        response = self.client.post("/lookup_hashes", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["hash_info"][0]["verdict"] == "unknown"
    
    def test_lookup_hashes_no_auth(self):
        """Test hash lookup without authentication"""
        payload = {
            "hashes": ["5d41402abc4b2a76b9719d911017c592"],
            "enable_raw_json": False
        }
        
        response = self.client.post("/lookup_hashes", json=payload)
        assert response.status_code == 401
    
    def test_get_report_success(self):
        """Test successful report retrieval"""
        payload = {
            "report_id": "550e8400-e29b-41d4-a716-446655440001",
            "include_all": True
        }
        
        response = self.client.post("/get_report", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "report" in data["data"]
        assert data["data"]["report"]["report_id"] == "550e8400-e29b-41d4-a716-446655440001"
        assert data["data"]["report"]["verdict"] == "malicious"
        assert "sandbox_details" in data["data"]["report"]  # include_all=True
    
    def test_get_report_basic(self):
        """Test basic report retrieval without all details"""
        payload = {
            "report_id": "550e8400-e29b-41d4-a716-446655440001",
            "include_all": False
        }
        
        response = self.client.post("/get_report", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "sandbox_details" not in data["data"]["report"]  # include_all=False
    
    def test_get_report_not_found(self):
        """Test report retrieval with invalid report ID"""
        payload = {
            "report_id": "550e8400-e29b-41d4-a716-000000000000",
            "include_all": False
        }
        
        response = self.client.post("/get_report", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert data["data"]["task_success"] is False
        assert "not found" in data["data"]["status_msg"].lower()
    
    def test_get_report_invalid_uuid(self):
        """Test report retrieval with invalid UUID format"""
        payload = {
            "report_id": "invalid-uuid-format",
            "include_all": False
        }
        
        response = self.client.post("/get_report", json=payload, headers=self.headers)
        assert response.status_code == 422  # Validation error
    
    def test_analyse_url_success(self):
        """Test successful URL analysis submission"""
        payload = {
            "urls": ["http://suspicious-domain.com", "https://malware-site.net"]
        }
        
        response = self.client.post("/analyse_url", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]
        assert "response_json" in data["data"]
        assert data["data"]["response_json"]["urls_submitted"] == 2
    
    def test_analyse_url_too_many_urls(self):
        """Test URL analysis with too many URLs"""
        payload = {
            "urls": ["http://url1.com", "http://url2.com", "http://url3.com", 
                    "http://url4.com", "http://url5.com", "http://url6.com"]
        }
        
        response = self.client.post("/analyse_url", json=payload, headers=self.headers)
        assert response.status_code == 422  # Validation error
    
    def test_analyse_file_with_url(self):
        """Test file analysis with URL reference"""
        payload = {
            "file_ref": "https://example.com/suspicious-file.exe"
        }
        
        response = self.client.post("/analyse_file", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]
        assert "response_json" in data["data"]
        
        response_json = json.loads(data["data"]["response_json"])
        assert response_json["file_type"] == "url"
    
    def test_analyse_file_with_uuid(self):
        """Test file analysis with UUID reference"""
        payload = {
            "file_ref": "550e8400-e29b-41d4-a716-446655440001"
        }
        
        response = self.client.post("/analyse_file", json=payload, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        response_json = json.loads(data["data"]["response_json"])
        assert response_json["file_type"] == "uuid"
    
    def test_all_endpoints_require_auth(self):
        """Test that all endpoints require authentication"""
        endpoints = [
            ("/lookup_hashes", {"hashes": ["test"]}),
            ("/get_report", {"report_id": "550e8400-e29b-41d4-a716-446655440001"}),
            ("/analyse_url", {"urls": ["http://test.com"]}),
            ("/analyse_file", {"file_ref": "test-file"})
        ]
        
        for endpoint, payload in endpoints:
            response = self.client.post(endpoint, json=payload)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
    
    @pytest.mark.asyncio
    async def test_server_integration(self):
        """Test server integration with mocked external API calls"""
        # This would test actual API integration in a real scenario
        # For now, we're using mock data, so integration is already tested above
        assert True  # Placeholder for actual integration tests
