
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
import json
from src.client.mcp_client import MCPClient

class TestMCPClient:
    """Test cases for MCPClient"""
    
    @pytest.mark.asyncio
    async def test_init(self, mock_server_configs):
        """Test MCPClient initialization"""
        client = MCPClient(mock_server_configs)
        assert client.server_configs == mock_server_configs
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_get_session(self, mock_server_configs):
        """Test session creation"""
        client = MCPClient(mock_server_configs)
        session = await client.get_session()
        assert isinstance(session, aiohttp.ClientSession)
        assert client.session is not None
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_server_success(self, mock_server_configs, mock_virustotal_response):
        """Test successful server call"""
        client = MCPClient(mock_server_configs)
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_virustotal_response)
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client.session = mock_session
        
        result = await client.call_server("virustotal", "ip_report", {"ip": "192.168.1.100"})
        
        assert result == mock_virustotal_response
        mock_session.post.assert_called_once()
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_server_unknown_server(self, mock_server_configs):
        """Test calling unknown server"""
        client = MCPClient(mock_server_configs)
        
        with pytest.raises(ValueError, match="Unknown server: unknown"):
            await client.call_server("unknown", "test_action", {})
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_server_error_response(self, mock_server_configs):
        """Test server error response"""
        client = MCPClient(mock_server_configs)
        
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client.session = mock_session
        
        with pytest.raises(Exception, match="Server virustotal returned 500"):
            await client.call_server("virustotal", "ip_report", {"ip": "192.168.1.100"})
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_get_server_capabilities(self, mock_server_configs):
        """Test getting server capabilities"""
        client = MCPClient(mock_server_configs)
        
        capabilities = {
            "server_name": "virustotal",
            "version": "1.0.0",
            "capabilities": ["ip_report", "domain_report"]
        }
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=capabilities)
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        client.session = mock_session
        
        result = await client.get_server_capabilities("virustotal")
        assert result == capabilities
        await client.close()
    
    @pytest.mark.asyncio
    async def test_test_all_servers(self, mock_server_configs):
        """Test testing all servers"""
        client = MCPClient(mock_server_configs)
        
        # Mock successful response for all servers
        capabilities = {"server_name": "test", "status": "online"}
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=capabilities)
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        client.session = mock_session
        
        results = await client.test_all_servers()
        
        assert len(results) == len(mock_server_configs)
        for server_name in mock_server_configs:
            assert server_name in results
            assert results[server_name]["status"] == "online"
        
        await client.close()
