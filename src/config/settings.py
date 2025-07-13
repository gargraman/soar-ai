
import json
from typing import Dict, Any

class AppConfig:
    """Application configuration management"""
    
    def __init__(self):
        self.mcp_servers = {
            "virustotal": {
                "base_url": "http://0.0.0.0:8001",
                "capabilities": ["ip_report", "domain_report"],
                "auth_headers": {
                    "X-API-Key": "your-virustotal-api-key"
                }
            },
            "servicenow": {
                "base_url": "http://0.0.0.0:8002", 
                "capabilities": ["create_record", "get_record"],
                "auth_headers": {
                    "Authorization": "Basic your-servicenow-auth"
                }
            },
            "cyberreason": {
                "base_url": "http://0.0.0.0:8003",
                "capabilities": ["get_pylum_id", "check_terminal_status"],
                "auth_headers": {
                    "Authorization": "Bearer your-cyberreason-token"
                }
            },
            "custom_rest": {
                "base_url": "http://0.0.0.0:8004",
                "capabilities": ["custom_enrichment"],
                "auth_headers": {}
            }
        }
        
        self.kafka_config = {
            "bootstrap_servers": ["localhost:9092"],
            "security_protocol": "PLAINTEXT",
            "auto_offset_reset": "latest"
        }
        
        self.ai_config = {
            "provider": "aws_bedrock",
            "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "region": "us-east-1",
            "max_tokens": 2000,
            "temperature": 0.1,
            "fallback_to_rules": True
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "mcp_servers": self.mcp_servers,
            "kafka_config": self.kafka_config,
            "ai_config": self.ai_config
        }
        
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_from_file(cls, file_path: str):
        """Load configuration from JSON file"""
        config = cls()
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                config.mcp_servers = data.get("mcp_servers", config.mcp_servers)
                config.kafka_config = data.get("kafka_config", config.kafka_config)
                config.ai_config = data.get("ai_config", config.ai_config)
        except FileNotFoundError:
            pass  # Use default configuration
        return config
