import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'client')))

from ai_provider import (
    AWSBedrockProvider, 
    GoogleVertexProvider, 
    GoogleVertexGeminiProvider,
    AIProviderFactory, 
    RuleBasedFallback
)

class TestAWSBedrockProvider:
    """Test cases for AWS Bedrock provider"""
    
    @pytest.fixture
    def provider_config(self):
        return {
            "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "region": "us-east-1",
            "max_tokens": 2000,
            "temperature": 0.1
        }
    
    @pytest.fixture
    def provider(self, provider_config):
        return AWSBedrockProvider(provider_config)
    
    @patch('boto3.client')
    def test_bedrock_client_initialization(self, mock_boto3_client, provider):
        """Test Bedrock client initialization"""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        client = provider._get_bedrock_client()
        
        mock_boto3_client.assert_called_once_with(
            'bedrock-runtime', 
            region_name='us-east-1'
        )
        assert client == mock_client
        assert provider._bedrock_client == mock_client
    
    @patch('boto3.client')
    async def test_analyze_security_event_success(self, mock_boto3_client, provider):
        """Test successful security event analysis"""
        # Mock Bedrock client and response
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': json.dumps({
                    "actions": [
                        {
                            "server": "virustotal",
                            "action": "ip_report",
                            "parameters": {"ip": "192.168.1.100"}
                        }
                    ],
                    "reasoning": "Suspicious IP detected, checking reputation",
                    "severity": "medium",
                    "priority": 3
                })
            }]
        }).encode()
        
        mock_client.invoke_model.return_value = mock_response
        
        event_data = {"src_ip": "192.168.1.100", "event_type": "network_connection"}
        user_prompt = "Check if this IP is malicious"
        
        result = await provider.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"][0]["server"] == "virustotal"
        assert result["actions"][0]["action"] == "ip_report"
        assert result["severity"] == "medium"
        assert result["priority"] == 3
        
        # Verify model was called with correct parameters
        mock_client.invoke_model.assert_called_once()
        call_args = mock_client.invoke_model.call_args
        assert call_args[1]['modelId'] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    @patch('boto3.client')
    async def test_analyze_security_event_non_json_response(self, mock_boto3_client, provider):
        """Test handling of non-JSON response"""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': "This is a plain text response without JSON"
            }]
        }).encode()
        
        mock_client.invoke_model.return_value = mock_response
        
        event_data = {"src_ip": "192.168.1.100"}
        user_prompt = "Check if this IP is malicious"
        
        result = await provider.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"] == []
        assert result["reasoning"] == "This is a plain text response without JSON"
        assert result["severity"] == "medium"
        assert result["priority"] == 3
    
    @patch('boto3.client')
    def test_is_available_success(self, mock_boto3_client, provider):
        """Test is_available returns True when properly configured"""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        assert provider.is_available() is True
    
    @patch('boto3.client')
    def test_is_available_failure(self, mock_boto3_client, provider):
        """Test is_available returns False when configuration fails"""
        mock_boto3_client.side_effect = Exception("Configuration error")
        
        assert provider.is_available() is False


class TestGoogleVertexProvider:
    """Test cases for Google Vertex AI Claude provider"""
    
    @pytest.fixture
    def provider_config(self):
        return {
            "model": "claude-3-5-sonnet@20241022",
            "project_id": "test-project",
            "location": "us-central1",
            "max_tokens": 2000,
            "temperature": 0.1
        }
    
    @pytest.fixture
    def provider(self, provider_config):
        return GoogleVertexProvider(provider_config)
    
    @patch('ai_provider.AnthropicVertex')
    def test_vertex_client_initialization(self, mock_anthropic_vertex, provider):
        """Test Vertex AI client initialization"""
        mock_client = Mock()
        mock_anthropic_vertex.return_value = mock_client
        
        client = provider._get_vertex_client()
        
        mock_anthropic_vertex.assert_called_once_with(
            project_id='test-project',
            region='us-central1'
        )
        assert client == mock_client
        assert provider._vertex_client == mock_client
    
    @patch('ai_provider.AnthropicVertex')
    async def test_analyze_security_event_success(self, mock_anthropic_vertex, provider):
        """Test successful security event analysis"""
        mock_client = Mock()
        mock_anthropic_vertex.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "actions": [
                {
                    "server": "servicenow",
                    "action": "create_record",
                    "parameters": {
                        "type": "incident",
                        "summary": "High severity security event"
                    }
                }
            ],
            "reasoning": "High severity event requires immediate attention",
            "severity": "high",
            "priority": 4
        })
        
        mock_client.messages.create.return_value = mock_response
        
        event_data = {"event_type": "malware_detected", "severity": "high"}
        user_prompt = "Create a ticket for this high severity event"
        
        result = await provider.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"][0]["server"] == "servicenow"
        assert result["severity"] == "high"
        assert result["priority"] == 4


class TestGoogleVertexGeminiProvider:
    """Test cases for Google Vertex AI Gemini provider"""
    
    @pytest.fixture
    def provider_config(self):
        return {
            "model": "gemini-1.5-pro",
            "project_id": "test-project",
            "location": "us-central1",
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40
        }
    
    @pytest.fixture
    def provider(self, provider_config):
        return GoogleVertexGeminiProvider(provider_config)
    
    @patch('ai_provider.vertexai.init')
    @patch('ai_provider.GenerativeModel')
    @patch('ai_provider.GenerationConfig')
    def test_model_initialization(self, mock_generation_config, mock_generative_model, mock_vertexai_init, provider):
        """Test Vertex AI Gemini model initialization"""
        mock_model = Mock()
        mock_generative_model.return_value = mock_model
        mock_config = Mock()
        mock_generation_config.return_value = mock_config
        
        model = provider._get_model()
        
        # Verify vertexai.init was called
        mock_vertexai_init.assert_called_once_with(
            project='test-project',
            location='us-central1'
        )
        
        # Verify GenerationConfig was created with correct parameters
        mock_generation_config.assert_called_once_with(
            max_output_tokens=2000,
            temperature=0.1,
            top_p=0.8,
            top_k=40
        )
        
        # Verify GenerativeModel was created
        mock_generative_model.assert_called_once_with(
            model_name='gemini-1.5-pro',
            generation_config=mock_config
        )
        
        assert model == mock_model
        assert provider._model == mock_model
    
    @patch('ai_provider.vertexai.init')
    @patch('ai_provider.GenerativeModel')
    @patch('ai_provider.GenerationConfig')
    async def test_analyze_security_event_success(self, mock_generation_config, mock_generative_model, mock_vertexai_init, provider):
        """Test successful security event analysis with Gemini"""
        mock_model = Mock()
        mock_generative_model.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = json.dumps({
            "actions": [
                {
                    "server": "cyberreason",
                    "action": "get_pylum_id",
                    "parameters": {"hostname": "workstation-01"}
                }
            ],
            "reasoning": "Endpoint investigation required for suspicious activity",
            "severity": "medium",
            "priority": 3
        })
        
        mock_model.generate_content.return_value = mock_response
        
        event_data = {"hostname": "workstation-01", "event_type": "suspicious_process"}
        user_prompt = "Investigate this endpoint for threats"
        
        result = await provider.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"][0]["server"] == "cyberreason"
        assert result["actions"][0]["action"] == "get_pylum_id"
        assert result["severity"] == "medium"
        assert result["priority"] == 3
        
        # Verify generate_content was called
        mock_model.generate_content.assert_called_once()
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Security Event Data:" in call_args
        assert "workstation-01" in call_args
    
    @patch('ai_provider.vertexai.init')
    @patch('ai_provider.GenerativeModel')
    @patch('ai_provider.GenerationConfig')
    async def test_analyze_security_event_non_json_response(self, mock_generation_config, mock_generative_model, mock_vertexai_init, provider):
        """Test handling of non-JSON response from Gemini"""
        mock_model = Mock()
        mock_generative_model.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = "This is a plain text analysis without JSON format"
        
        mock_model.generate_content.return_value = mock_response
        
        event_data = {"src_ip": "192.168.1.100"}
        user_prompt = "Analyze this event"
        
        result = await provider.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"] == []
        assert result["reasoning"] == "This is a plain text analysis without JSON format"
        assert result["severity"] == "medium"
        assert result["priority"] == 3
    
    @patch('ai_provider.vertexai.init')
    @patch('ai_provider.GenerativeModel')
    @patch('ai_provider.GenerationConfig')
    def test_is_available_success(self, mock_generation_config, mock_generative_model, mock_vertexai_init, provider):
        """Test is_available returns True when properly configured"""
        mock_model = Mock()
        mock_generative_model.return_value = mock_model
        
        assert provider.is_available() is True
    
    @patch('ai_provider.vertexai.init')
    def test_is_available_failure(self, mock_vertexai_init, provider):
        """Test is_available returns False when configuration fails"""
        mock_vertexai_init.side_effect = Exception("Configuration error")
        
        assert provider.is_available() is False


class TestAIProviderFactory:
    """Test cases for AI Provider Factory"""
    
    def test_create_aws_bedrock_provider(self):
        """Test creating AWS Bedrock provider"""
        ai_config = {
            "provider": "aws_bedrock",
            "aws_bedrock": {
                "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "region": "us-east-1"
            }
        }
        
        provider = AIProviderFactory.create_provider(ai_config)
        
        assert isinstance(provider, AWSBedrockProvider)
        assert provider.config["model"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert provider.config["region"] == "us-east-1"
    
    def test_create_google_vertex_provider(self):
        """Test creating Google Vertex AI provider"""
        ai_config = {
            "provider": "google_vertex",
            "google_vertex": {
                "model": "claude-3-5-sonnet@20241022",
                "project_id": "test-project"
            }
        }
        
        provider = AIProviderFactory.create_provider(ai_config)
        
        assert isinstance(provider, GoogleVertexProvider)
        assert provider.config["model"] == "claude-3-5-sonnet@20241022"
        assert provider.config["project_id"] == "test-project"
    
    def test_create_google_vertex_gemini_provider(self):
        """Test creating Google Vertex AI Gemini provider"""
        ai_config = {
            "provider": "google_vertex_gemini",
            "google_vertex_gemini": {
                "model": "gemini-1.5-pro",
                "project_id": "test-project",
                "top_p": 0.8
            }
        }
        
        provider = AIProviderFactory.create_provider(ai_config)
        
        assert isinstance(provider, GoogleVertexGeminiProvider)
        assert provider.config["model"] == "gemini-1.5-pro"
        assert provider.config["project_id"] == "test-project"
        assert provider.config["top_p"] == 0.8
    
    def test_create_unknown_provider(self):
        """Test error handling for unknown provider"""
        ai_config = {
            "provider": "unknown_provider"
        }
        
        with pytest.raises(ValueError, match="Unknown AI provider: unknown_provider"):
            AIProviderFactory.create_provider(ai_config)
    
    @patch.object(AWSBedrockProvider, 'is_available')
    @patch.object(GoogleVertexProvider, 'is_available')
    @patch.object(GoogleVertexGeminiProvider, 'is_available')
    def test_get_available_providers(self, mock_gemini_available, mock_vertex_available, mock_bedrock_available):
        """Test getting list of available providers"""
        mock_bedrock_available.return_value = True
        mock_vertex_available.return_value = False
        mock_gemini_available.return_value = True
        
        ai_config = {
            "aws_bedrock": {"region": "us-east-1"},
            "google_vertex": {"project_id": "test-project"},
            "google_vertex_gemini": {"project_id": "test-project"}
        }
        
        available = AIProviderFactory.get_available_providers(ai_config)
        
        assert "aws_bedrock" in available
        assert "google_vertex" not in available  # Mock returns False
        assert "google_vertex_gemini" in available
        assert len(available) == 2


class TestRuleBasedFallback:
    """Test cases for rule-based fallback"""
    
    def test_rule_based_analysis_with_all_servers(self):
        """Test rule-based analysis that triggers all MCP servers"""
        event_data = {
            "src_ip": "192.168.1.100",
            "domain": "suspicious-site.com",
            "file_hash": "abc123def456",
            "hostname": "workstation-01",
            "event_type": "critical_malware_detection"
        }
        user_prompt = "investigate this malicious endpoint and create a ticket"
        
        result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
        
        # Should have actions for all servers
        servers_used = [action["server"] for action in result["actions"]]
        assert "virustotal" in servers_used
        assert "servicenow" in servers_used
        assert "cyberreason" in servers_used
        
        assert result["severity"] == "high"  # Critical event
        assert result["priority"] == 4
        assert result["fallback_used"] is True
    
    def test_rule_based_analysis_virustotal_only(self):
        """Test rule-based analysis for VirusTotal only"""
        event_data = {"src_ip": "8.8.8.8"}
        user_prompt = "check reputation of this IP"
        
        result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
        
        assert len(result["actions"]) == 1
        assert result["actions"][0]["server"] == "virustotal"
        assert result["actions"][0]["action"] == "ip_report"
        assert result["actions"][0]["parameters"]["ip"] == "8.8.8.8"
    
    def test_rule_based_analysis_no_actions(self):
        """Test rule-based analysis with no matching actions"""
        event_data = {"timestamp": "2023-01-01T00:00:00Z"}
        user_prompt = "what happened here"
        
        result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
        
        assert result["actions"] == []
        assert result["severity"] == "medium"
        assert result["priority"] == 3


if __name__ == "__main__":
    pytest.main([__file__])
