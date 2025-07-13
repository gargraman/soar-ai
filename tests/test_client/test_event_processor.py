
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import boto3
from src.client.event_processor import EventProcessor
from src.client.mcp_client import MCPClient

class TestEventProcessor:
    """Test cases for EventProcessor"""
    
    def test_init(self, mock_server_configs):
        """Test EventProcessor initialization"""
        mock_mcp_client = MagicMock()
        
        with patch('boto3.client') as mock_boto:
            processor = EventProcessor(mock_mcp_client)
            assert processor.mcp_client == mock_mcp_client
            assert processor.claude_model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0"
            mock_boto.assert_called_once_with('bedrock-runtime', region_name='us-east-1')
    
    def test_extract_event_attributes(self, mock_server_configs, sample_event_data):
        """Test event attribute extraction"""
        mock_mcp_client = MagicMock()
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            attributes = processor.extract_event_attributes(sample_event_data)
            
            assert attributes["event_type"] == "malware_detection"
            assert attributes["severity"] == "high"
            assert "192.168.1.100" in attributes["indicators"]["ips"]
            assert "malicious-domain.com" in attributes["indicators"]["domains"]
            assert attributes["host_info"]["hostname"] == "workstation-01"
    
    def test_extract_event_attributes_with_hashes(self, mock_server_configs):
        """Test hash extraction from event data"""
        mock_mcp_client = MagicMock()
        
        event_data = {
            "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
            "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            attributes = processor.extract_event_attributes(event_data)
            
            assert "md5" in attributes["indicators"]
            assert "sha256" in attributes["indicators"]
            assert "d41d8cd98f00b204e9800998ecf8427e" in attributes["indicators"]["md5"]
    
    @pytest.mark.asyncio
    async def test_process_event(self, mock_server_configs, sample_event_data, mock_bedrock_client):
        """Test complete event processing"""
        mock_mcp_client = AsyncMock()
        mock_mcp_client.call_server.return_value = {"success": True, "data": {"threat_score": 85}}
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            result = await processor.process_event(sample_event_data, "Check if this IP is malicious")
            
            assert "event_id" in result
            assert "analysis" in result
            assert "results" in result
            assert result["user_prompt"] == "Check if this IP is malicious"
    
    @pytest.mark.asyncio
    async def test_analyze_with_claude(self, mock_server_configs, sample_event_data, sample_event_attributes, mock_bedrock_client):
        """Test Claude analysis"""
        mock_mcp_client = MagicMock()
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            analysis = await processor.analyze_with_claude(
                sample_event_data, 
                sample_event_attributes, 
                "Check if this IP is malicious"
            )
            
            assert "determined_actions" in analysis
            assert "reasoning" in analysis
            assert "severity_assessment" in analysis
            assert analysis["ai_model"] == "claude-3.5-sonnet"
    
    @pytest.mark.asyncio
    async def test_analyze_with_claude_fallback(self, mock_server_configs, sample_event_data, sample_event_attributes):
        """Test Claude analysis fallback"""
        mock_mcp_client = MagicMock()
        mock_bedrock_client = MagicMock()
        mock_bedrock_client.invoke_model.side_effect = Exception("AWS Error")
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            analysis = await processor.analyze_with_claude(
                sample_event_data,
                sample_event_attributes, 
                "Check if this IP is malicious"
            )
            
            assert analysis["ai_model"] == "rule-based-fallback"
            assert "fallback" in analysis["reasoning"].lower()
    
    def test_fallback_analysis(self, mock_server_configs, sample_event_attributes):
        """Test fallback rule-based analysis"""
        mock_mcp_client = MagicMock()
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            
            # Test malicious IP prompt
            analysis = processor.fallback_analysis(sample_event_attributes, "check if this IP is malicious")
            
            assert len(analysis["determined_actions"]) > 0
            assert any(action["server"] == "virustotal" for action in analysis["determined_actions"])
            
            # Test incident creation prompt
            analysis = processor.fallback_analysis(sample_event_attributes, "create a ServiceNow ticket")
            
            assert any(action["server"] == "servicenow" for action in analysis["determined_actions"])
    
    def test_evaluate_condition(self, mock_server_configs):
        """Test condition evaluation"""
        mock_mcp_client = MagicMock()
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            
            # Test threat score condition
            dependency_result = {
                "success": True,
                "result": {"threat_score": 85}
            }
            
            assert processor.evaluate_condition("threat_score > 70", dependency_result)
            assert not processor.evaluate_condition("threat_score > 90", dependency_result)
            
            # Test severity condition
            dependency_result["result"] = {"severity": "high"}
            assert processor.evaluate_condition("severity high", dependency_result)
            
            # Test compromised condition
            dependency_result["result"] = {"status": "compromised"}
            assert processor.evaluate_condition("compromised", dependency_result)
    
    @pytest.mark.asyncio
    async def test_execute_actions(self, mock_server_configs, sample_event_data):
        """Test action execution"""
        mock_mcp_client = AsyncMock()
        mock_mcp_client.call_server.return_value = {"success": True, "data": {"threat_score": 85}}
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            
            analysis = {
                "determined_actions": [
                    {
                        "step": 1,
                        "server": "virustotal",
                        "action": "ip_report",
                        "parameters": {"ip": "192.168.1.100"},
                        "priority": "high",
                        "rationale": "Check IP reputation"
                    }
                ]
            }
            
            results = await processor.execute_actions(sample_event_data, analysis)
            
            assert len(results) == 1
            assert results[0]["success"]
            assert results[0]["step"] == 1
            mock_mcp_client.call_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_actions_with_dependencies(self, mock_server_configs, sample_event_data):
        """Test action execution with dependencies"""
        mock_mcp_client = AsyncMock()
        
        # First call returns threat score, second call creates incident
        mock_mcp_client.call_server.side_effect = [
            {"success": True, "data": {"threat_score": 85}},
            {"success": True, "data": {"record_id": "INC123"}}
        ]
        
        with patch('boto3.client'):
            processor = EventProcessor(mock_mcp_client)
            
            analysis = {
                "determined_actions": [
                    {
                        "step": 1,
                        "server": "virustotal", 
                        "action": "ip_report",
                        "parameters": {"ip": "192.168.1.100"},
                        "priority": "high",
                        "rationale": "Check IP reputation"
                    },
                    {
                        "step": 2,
                        "server": "servicenow",
                        "action": "create_record", 
                        "parameters": {"type": "incident", "summary": "Test"},
                        "depends_on": 1,
                        "condition": "threat_score > 70",
                        "priority": "high",
                        "rationale": "Create incident if threat detected"
                    }
                ]
            }
            
            results = await processor.execute_actions(sample_event_data, analysis)
            
            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert mock_mcp_client.call_server.call_count == 2
