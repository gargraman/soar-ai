import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'client')))

from ai_provider import (
    AWSBedrockProvider, 
    GoogleVertexProvider, 
    GoogleVertexGeminiProvider,
    AIProviderFactory, 
    RuleBasedFallback
)

class TestGoogleVertexGeminiProviderBasic:
    """Basic test cases for Google Vertex AI Gemini provider without external dependencies"""
    
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
    
    def test_provider_initialization(self, provider, provider_config):
        """Test provider initialization with config"""
        assert provider.config == provider_config
        assert provider._model is None
    
    def test_provider_config_defaults(self):
        """Test provider with minimal config uses defaults"""
        minimal_config = {
            "project_id": "test-project"
        }
        provider = GoogleVertexGeminiProvider(minimal_config)
        assert provider.config["project_id"] == "test-project"


class TestAIProviderFactoryWithGemini:
    """Test AI Provider Factory with the new Gemini provider"""
    
    def test_create_google_vertex_gemini_provider(self):
        """Test creating Google Vertex AI Gemini provider via factory"""
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
    
    def test_provider_registry_includes_gemini(self):
        """Test that the provider registry includes the new Gemini provider"""
        providers = AIProviderFactory._providers
        
        assert "aws_bedrock" in providers
        assert "google_vertex" in providers
        assert "google_vertex_gemini" in providers
        
        assert providers["aws_bedrock"] == AWSBedrockProvider
        assert providers["google_vertex"] == GoogleVertexProvider
        assert providers["google_vertex_gemini"] == GoogleVertexGeminiProvider
    
    def test_unknown_provider_error(self):
        """Test error handling for unknown provider"""
        ai_config = {
            "provider": "unknown_provider"
        }
        
        with pytest.raises(ValueError, match="Unknown AI provider: unknown_provider"):
            AIProviderFactory.create_provider(ai_config)


class TestRuleBasedFallbackExtended:
    """Extended test cases for rule-based fallback"""
    
    def test_rule_based_comprehensive_analysis(self):
        """Test rule-based analysis with comprehensive event data"""
        event_data = {
            "src_ip": "192.168.1.100",
            "dst_ip": "8.8.8.8", 
            "domain": "suspicious-site.com",
            "file_hash": "abc123def456",
            "hostname": "workstation-01",
            "event_type": "critical_malware_detection",
            "severity": "critical"
        }
        user_prompt = "investigate this malicious endpoint, check reputation, and create a ticket"
        
        result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
        
        # Should have actions for multiple servers
        servers_used = [action["server"] for action in result["actions"]]
        assert "virustotal" in servers_used
        assert "servicenow" in servers_used
        assert "cyberreason" in servers_used
        
        # Check for VirusTotal actions
        vt_actions = [a for a in result["actions"] if a["server"] == "virustotal"]
        assert len(vt_actions) >= 2  # Should have IP and domain checks
        
        # Check action types
        action_types = [a["action"] for a in vt_actions]
        assert "ip_report" in action_types
        assert "domain_report" in action_types
        
        assert result["severity"] == "high"  # Critical event maps to high
        assert result["priority"] == 4
        assert result["fallback_used"] is True
    
    def test_rule_based_file_hash_analysis(self):
        """Test rule-based analysis specifically for file hashes"""
        test_cases = [
            {"file_hash": "abc123def456", "expected_hash": "abc123def456"},
            {"hash": "def456ghi789", "expected_hash": "def456ghi789"},
            {"sha256": "a1b2c3d4e5f6", "expected_hash": "a1b2c3d4e5f6"},
            {"sha1": "1a2b3c4d5e6f", "expected_hash": "1a2b3c4d5e6f"},
            {"md5": "abcdef123456", "expected_hash": "abcdef123456"}
        ]
        
        for test_case in test_cases:
            event_data = test_case.copy()
            expected_hash = event_data.pop("expected_hash")
            user_prompt = "analyze this file hash"
            
            result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
            
            # Should have VirusTotal file report action
            vt_actions = [a for a in result["actions"] if a["server"] == "virustotal" and a["action"] == "file_report"]
            assert len(vt_actions) == 1
            assert vt_actions[0]["parameters"]["hash"] == expected_hash
    
    def test_rule_based_custom_rest_integration(self):
        """Test rule-based analysis triggers custom REST integration"""
        event_data = {
            "src_ip": "192.168.1.100",
            "custom_field": "threat_intel_needed"
        }
        user_prompt = "enrich this event with custom threat intelligence"
        
        result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
        
        # Should have custom REST action
        custom_actions = [a for a in result["actions"] if a["server"] == "custom_rest"]
        assert len(custom_actions) == 1
        assert custom_actions[0]["action"] == "enrich_event"
        assert custom_actions[0]["parameters"] == event_data


class TestProviderComparison:
    """Test comparison between different providers"""
    
    def test_provider_interface_consistency(self):
        """Test that all providers implement the same interface"""
        configs = {
            "aws_bedrock": {"region": "us-east-1", "model": "test-model"},
            "google_vertex": {"project_id": "test-project", "model": "test-model"},
            "google_vertex_gemini": {"project_id": "test-project", "model": "gemini-1.5-pro"}
        }
        
        for provider_type, config in configs.items():
            provider_class = AIProviderFactory._providers[provider_type]
            provider = provider_class(config)
            
            # Check that all providers have required methods
            assert hasattr(provider, 'analyze_security_event')
            assert hasattr(provider, 'is_available')
            assert callable(provider.analyze_security_event)
            assert callable(provider.is_available)
            
            # Check that config is stored
            assert provider.config == config
    
    def test_gemini_provider_specific_config(self):
        """Test Gemini provider specific configuration parameters"""
        config = {
            "model": "gemini-1.5-pro",
            "project_id": "test-project",
            "location": "us-central1",
            "max_tokens": 4000,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 50
        }
        
        provider = GoogleVertexGeminiProvider(config)
        
        # Test that Gemini-specific parameters are preserved
        assert provider.config.get("top_p") == 0.9
        assert provider.config.get("top_k") == 50
        assert provider.config.get("max_tokens") == 4000
        
        # Compare with other providers that don't have these parameters
        aws_provider = AWSBedrockProvider({"region": "us-east-1"})
        vertex_provider = GoogleVertexProvider({"project_id": "test-project"})
        
        # AWS and Vertex providers shouldn't have Gemini-specific params
        assert "top_p" not in aws_provider.config
        assert "top_k" not in aws_provider.config
        assert "top_p" not in vertex_provider.config
        assert "top_k" not in vertex_provider.config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
