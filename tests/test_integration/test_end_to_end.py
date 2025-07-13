
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.client.mcp_client import MCPClient
from src.client.event_processor import EventProcessor

class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def mock_server_responses(self):
        """Mock responses from all servers"""
        return {
            "virustotal_ip": {
                "success": True,
                "data": {
                    "ip": "192.168.1.100",
                    "reputation": "malicious",
                    "threat_score": 85,
                    "detections": 15,
                    "total_engines": 20
                }
            },
            "servicenow_create": {
                "success": True,
                "data": {
                    "record_id": "INC12345678",
                    "type": "incident",
                    "summary": "Security event detected",
                    "status": "New"
                }
            },
            "cyberreason_status": {
                "success": True,
                "data": {
                    "hostname": "workstation-01",
                    "pylum_id": "PYL_12345678",
                    "status": "compromised",
                    "threat_level": "high",
                    "is_compromised": True
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_security_investigation_flow(self, 
                                                       mock_server_configs,
                                                       sample_event_data,
                                                       mock_server_responses,
                                                       mock_bedrock_client):
        """Test complete security investigation workflow"""
        
        # Setup mock MCP client
        mock_mcp_client = AsyncMock()
        
        # Configure call responses based on server and action
        def mock_call_server(server, action, params):
            if server == "virustotal" and action == "ip_report":
                return mock_server_responses["virustotal_ip"]
            elif server == "servicenow" and action == "create_record":
                return mock_server_responses["servicenow_create"]
            elif server == "cyberreason" and action == "check_terminal_status":
                return mock_server_responses["cyberreason_status"]
            else:
                return {"success": False, "error": "Unknown action"}
        
        mock_mcp_client.call_server.side_effect = mock_call_server
        
        # Setup event processor with mocked Claude
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            # Process a complex investigation prompt
            result = await processor.process_event(
                sample_event_data,
                "Investigate this security event: check IP reputation, create incident if malicious, and check endpoint status"
            )
            
            # Verify the complete flow
            assert result["event_id"] == "EVT-001"
            assert "analysis" in result
            assert "results" in result
            
            # Verify Claude was called for analysis
            mock_bedrock_client.invoke_model.assert_called_once()
            
            # Verify all expected MCP server calls were made
            assert mock_mcp_client.call_server.call_count >= 1
            
            # Check that results contain expected actions
            analysis = result["analysis"]
            assert len(analysis["determined_actions"]) > 0
            assert any(action["server"] == "virustotal" for action in analysis["determined_actions"])
    
    @pytest.mark.asyncio
    async def test_conditional_workflow_execution(self,
                                                 mock_server_configs,
                                                 sample_event_data,
                                                 mock_server_responses,
                                                 mock_bedrock_client):
        """Test conditional workflow where subsequent actions depend on threat score"""
        
        mock_mcp_client = AsyncMock()
        
        # Setup responses - high threat score should trigger incident creation
        mock_mcp_client.call_server.side_effect = [
            mock_server_responses["virustotal_ip"],  # High threat score
            mock_server_responses["servicenow_create"]  # Should trigger incident creation
        ]
        
        # Mock Claude to return a conditional workflow
        claude_response = {
            "reasoning": "IP shows high threat score, creating incident",
            "severity_assessment": "high",
            "flow_strategy": "Conditional escalation based on threat level",
            "determined_actions": [
                {
                    "step": 1,
                    "server": "virustotal",
                    "action": "ip_report",
                    "parameters": {"ip": "192.168.1.100"},
                    "priority": "high",
                    "rationale": "Check IP reputation first"
                },
                {
                    "step": 2,
                    "server": "servicenow",
                    "action": "create_record",
                    "parameters": {
                        "type": "incident",
                        "summary": "High-risk IP detected",
                        "description": "Malicious IP detected in network traffic"
                    },
                    "depends_on": 1,
                    "condition": "threat_score > 70",
                    "priority": "high",
                    "rationale": "Create incident if threat score is high"
                }
            ],
            "risk_indicators": ["malicious_ip"],
            "expected_flow_outcomes": ["IP analysis", "Incident creation"],
            "recommended_follow_up": "Monitor endpoint"
        }
        
        # Mock Claude response
        mock_bedrock_client.invoke_model.return_value = {
            'body': MagicMock()
        }
        mock_bedrock_client.invoke_model.return_value['body'].read.return_value = \
            f'{{"content": [{{"text": "{{\\"reasoning\\": \\"{claude_response["reasoning"]}\\", \\"severity_assessment\\": \\"{claude_response["severity_assessment"]}\\", \\"flow_strategy\\": \\"{claude_response["flow_strategy"]}\\", \\"determined_actions\\": {claude_response["determined_actions"]}, \\"risk_indicators\\": {claude_response["risk_indicators"]}, \\"expected_flow_outcomes\\": {claude_response["expected_flow_outcomes"]}, \\"recommended_follow_up\\": \\"{claude_response["recommended_follow_up"]}\\"}}"}]}}'.encode()
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            result = await processor.process_event(
                sample_event_data,
                "Check IP and create incident if threat score is high"
            )
            
            # Verify both actions were executed
            assert len(result["results"]) == 2
            
            # Verify first action was IP check
            assert result["results"][0]["action"]["server"] == "virustotal"
            assert result["results"][0]["success"]
            
            # Verify second action was incident creation (because condition was met)
            assert result["results"][1]["action"]["server"] == "servicenow"
            assert result["results"][1]["success"]
            assert not result["results"][1].get("skipped", False)
    
    @pytest.mark.asyncio
    async def test_failed_dependency_handling(self,
                                             mock_server_configs,
                                             sample_event_data,
                                             mock_bedrock_client):
        """Test handling of failed dependencies in workflow"""
        
        mock_mcp_client = AsyncMock()
        
        # First call fails, second should be skipped
        mock_mcp_client.call_server.side_effect = [
            Exception("VirusTotal API error"),
            {"success": True, "data": {"record_id": "INC123"}}
        ]
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            # Create analysis with dependent actions
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
                        "priority": "high",
                        "rationale": "Create incident based on IP analysis"
                    }
                ]
            }
            
            results = await processor.execute_actions(sample_event_data, analysis)
            
            # Verify first action failed
            assert len(results) == 2
            assert not results[0]["success"]
            assert "error" in results[0]
            
            # Verify second action was skipped due to dependency failure
            assert not results[1]["success"]
            assert results[1].get("skipped", False)
            assert "Dependency step" in results[1]["error"]
    
    @pytest.mark.asyncio
    async def test_parallel_enrichment_workflow(self,
                                              mock_server_configs,
                                              sample_event_data,
                                              mock_server_responses,
                                              mock_bedrock_client):
        """Test parallel enrichment followed by consolidated response"""
        
        mock_mcp_client = AsyncMock()
        
        # Mock multiple parallel calls
        mock_mcp_client.call_server.side_effect = [
            mock_server_responses["virustotal_ip"],  # IP check
            {  # Domain check
                "success": True,
                "data": {
                    "domain": "malicious-domain.com",
                    "reputation": "malicious",
                    "threat_score": 90
                }
            },
            mock_server_responses["servicenow_create"]  # Incident creation
        ]
        
        # Mock Claude to return parallel + sequential workflow
        claude_response = {
            "reasoning": "Multiple IOCs detected, running parallel enrichment",
            "severity_assessment": "high",
            "flow_strategy": "Parallel enrichment followed by incident creation",
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
                    "server": "virustotal",
                    "action": "domain_report",
                    "parameters": {"domain": "malicious-domain.com"},
                    "priority": "high", 
                    "rationale": "Check domain reputation"
                },
                {
                    "step": 3,
                    "server": "servicenow",
                    "action": "create_record",
                    "parameters": {
                        "type": "incident",
                        "summary": "Multiple malicious IOCs detected",
                        "description": "Both IP and domain show malicious indicators"
                    },
                    "depends_on": 1,  # Could depend on either 1 or 2
                    "condition": "threat_score > 70",
                    "priority": "critical",
                    "rationale": "Create high-priority incident"
                }
            ],
            "risk_indicators": ["malicious_ip", "malicious_domain"],
            "expected_flow_outcomes": ["IP analysis", "Domain analysis", "Incident creation"],
            "recommended_follow_up": "Investigate network traffic"
        }
        
        # Mock the Claude response properly
        mock_bedrock_client.invoke_model.return_value = {
            'body': MagicMock()
        }
        import json
        mock_bedrock_client.invoke_model.return_value['body'].read.return_value = \
            json.dumps({"content": [{"text": json.dumps(claude_response)}]}).encode()
        
        with patch('boto3.client', return_value=mock_bedrock_client):
            processor = EventProcessor(mock_mcp_client)
            
            result = await processor.process_event(
                sample_event_data,
                "Run comprehensive threat analysis on all IOCs and create incident if any are malicious"
            )
            
            # Verify all actions were executed
            assert len(result["results"]) == 3
            
            # Verify all actions succeeded
            for action_result in result["results"]:
                assert action_result["success"]
            
            # Verify the sequence: IP check, domain check, then incident
            assert result["results"][0]["action"]["action"] == "ip_report"
            assert result["results"][1]["action"]["action"] == "domain_report"  
            assert result["results"][2]["action"]["action"] == "create_record"
