
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import requests
import uvicorn
import yaml
import json

app = FastAPI(title="Custom REST Plugin MCP Server", version="1.0.0")

class APIConfiguration(BaseModel):
    name: str
    base_url: str
    headers: Optional[Dict[str, str]] = {}
    endpoints: Dict[str, Dict[str, Any]]

class RegisterAPIRequest(BaseModel):
    config: APIConfiguration

class CallEndpointRequest(BaseModel):
    api_name: str
    endpoint_name: str
    parameters: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Storage for registered APIs
registered_apis = {}

@app.get("/meta")
async def get_metadata():
    """Get server metadata and capabilities"""
    return {
        "server_name": "custom_rest",
        "version": "1.0.0",
        "capabilities": ["register_api", "call_endpoint", "list_apis"],
        "description": "Custom REST API wrapper generator from OpenAPI/Swagger specs",
        "authentication_required": False,
        "endpoints": {
            "register_api": {
                "method": "POST",
                "parameters": {"config": "APIConfiguration"},
                "description": "Register a new REST API configuration"
            },
            "call_endpoint": {
                "method": "POST", 
                "parameters": {
                    "api_name": "string",
                    "endpoint_name": "string",
                    "parameters": "object"
                },
                "description": "Call a registered API endpoint"
            },
            "list_apis": {
                "method": "GET",
                "description": "List all registered APIs"
            }
        }
    }

@app.post("/register_api", response_model=MCPResponse)
async def register_api(request: RegisterAPIRequest):
    """Register a new REST API configuration"""
    
    try:
        config = request.config
        api_name = config.name
        
        # Store the API configuration
        registered_apis[api_name] = {
            "base_url": config.base_url,
            "headers": config.headers,
            "endpoints": config.endpoints
        }
        
        return MCPResponse(success=True, data={
            "message": f"API '{api_name}' registered successfully",
            "endpoints": list(config.endpoints.keys())
        })
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/call_endpoint", response_model=MCPResponse)
async def call_endpoint(request: CallEndpointRequest):
    """Call a registered API endpoint"""
    
    try:
        api_name = request.api_name
        endpoint_name = request.endpoint_name
        parameters = request.parameters
        
        if api_name not in registered_apis:
            return MCPResponse(success=False, error=f"API '{api_name}' not registered")
            
        api_config = registered_apis[api_name]
        
        if endpoint_name not in api_config["endpoints"]:
            return MCPResponse(success=False, error=f"Endpoint '{endpoint_name}' not found in API '{api_name}'")
            
        endpoint_config = api_config["endpoints"][endpoint_name]
        
        # Build request
        base_url = api_config["base_url"]
        endpoint_path = endpoint_config.get("path", f"/{endpoint_name}")
        method = endpoint_config.get("method", "GET").upper()
        
        url = f"{base_url.rstrip('/')}{endpoint_path}"
        headers = api_config["headers"].copy()
        
        # Make the API call
        if method == "GET":
            response = requests.get(url, params=parameters, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=parameters, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=parameters, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, params=parameters, headers=headers)
        else:
            return MCPResponse(success=False, error=f"Unsupported HTTP method: {method}")
            
        # Parse response
        if response.status_code == 200:
            try:
                result_data = response.json()
            except:
                result_data = {"raw_response": response.text}
                
            return MCPResponse(success=True, data={
                "api_name": api_name,
                "endpoint_name": endpoint_name,
                "status_code": response.status_code,
                "response": result_data
            })
        else:
            return MCPResponse(success=False, error=f"API call failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.get("/list_apis")
async def list_apis():
    """List all registered APIs"""
    return {
        "registered_apis": {
            name: {
                "base_url": config["base_url"],
                "endpoints": list(config["endpoints"].keys())
            }
            for name, config in registered_apis.items()
        }
    }

@app.post("/register_from_openapi")
async def register_from_openapi(openapi_spec: Dict[str, Any], api_name: str):
    """Register API from OpenAPI/Swagger specification"""
    
    try:
        # Parse OpenAPI spec
        base_url = openapi_spec.get("servers", [{}])[0].get("url", "")
        paths = openapi_spec.get("paths", {})
        
        endpoints = {}
        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.lower() in ["get", "post", "put", "delete"]:
                    endpoint_name = spec.get("operationId", f"{method}_{path.replace('/', '_')}")
                    endpoints[endpoint_name] = {
                        "path": path,
                        "method": method.upper(),
                        "description": spec.get("summary", ""),
                        "parameters": spec.get("parameters", [])
                    }
                    
        # Register the API
        config = APIConfiguration(
            name=api_name,
            base_url=base_url,
            headers={},
            endpoints=endpoints
        )
        
        registered_apis[api_name] = {
            "base_url": config.base_url,
            "headers": config.headers,
            "endpoints": config.endpoints
        }
        
        return MCPResponse(success=True, data={
            "message": f"API '{api_name}' registered from OpenAPI spec",
            "endpoints": list(endpoints.keys())
        })
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
