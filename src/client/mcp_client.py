
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import json

class MCPClient:
    """Client for communicating with MCP servers"""
    
    def __init__(self, server_configs: Dict[str, Dict[str, Any]]):
        self.server_configs = server_configs
        self.session = None
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def call_server(self, server_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP server action"""
        
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {server_name}")
            
        server_config = self.server_configs[server_name]
        base_url = server_config["base_url"]
        
        # Build endpoint URL
        endpoint_url = f"{base_url}/{action}"
        
        session = await self.get_session()
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if "auth_headers" in server_config:
            headers.update(server_config["auth_headers"])
            
        try:
            async with session.post(endpoint_url, json=parameters, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Server {server_name} returned {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to {server_name}: {str(e)}")
            
    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Get server capabilities via /meta endpoint"""
        
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {server_name}")
            
        server_config = self.server_configs[server_name]
        base_url = server_config["base_url"]
        meta_url = f"{base_url}/meta"
        
        session = await self.get_session()
        
        try:
            async with session.get(meta_url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to get capabilities: {response.status}"}
                    
        except aiohttp.ClientError as e:
            return {"error": f"Failed to connect: {str(e)}"}
            
    async def test_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Test connectivity to all configured servers"""
        results = {}
        
        for server_name in self.server_configs:
            try:
                capabilities = await self.get_server_capabilities(server_name)
                results[server_name] = {
                    "status": "online",
                    "capabilities": capabilities
                }
            except Exception as e:
                results[server_name] = {
                    "status": "offline", 
                    "error": str(e)
                }
                
        return results
        
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
