from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    async def analyze_security_event(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """
        Analyze a security event and user prompt to determine appropriate actions
        
        Args:
            event_data: Security event data
            user_prompt: User's natural language prompt
            
        Returns:
            Dictionary containing analysis results and recommended actions
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is properly configured and available"""
        pass

class AWSBedrockProvider(AIProvider):
    """AWS Bedrock Claude implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._bedrock_client = None
        
    def _get_bedrock_client(self):
        """Initialize Bedrock client lazily"""
        if self._bedrock_client is None:
            try:
                import boto3
                self._bedrock_client = boto3.client(
                    'bedrock-runtime', 
                    region_name=self.config.get('region', 'us-east-1')
                )
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {e}")
                raise
        return self._bedrock_client
    
    async def analyze_security_event(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Analyze security event using AWS Bedrock Claude"""
        try:
            client = self._get_bedrock_client()
            
            system_prompt = """You are a cybersecurity expert analyzing security events and determining appropriate response actions.

Available MCP servers and their capabilities:
1. VirusTotal (virustotal): IP reputation, domain reputation, file analysis
2. ServiceNow (servicenow): Create incidents, manage tickets, track responses
3. CyberReason (cyberreason): Endpoint investigation, threat hunting, host analysis
4. Custom REST (custom_rest): Generic API integration for custom threat intelligence

Analyze the security event and user prompt to determine:
1. What actions should be taken
2. Which MCP servers to use
3. Priority and severity assessment
4. Detailed reasoning for decisions

Return a JSON response with:
- actions: List of recommended actions with server and parameters
- reasoning: Explanation of decision process
- severity: Event severity (low/medium/high/critical)
- priority: Response priority (1-5)"""

            user_message = f"""Security Event Data:
{json.dumps(event_data, indent=2)}

User Prompt: {user_prompt}

Please analyze this security event and provide recommendations."""

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.get('max_tokens', 2000),
                "temperature": self.config.get('temperature', 0.1),
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
            
            response = client.invoke_model(
                modelId=self.config.get('model', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, wrap in a basic structure
                return {
                    "actions": [],
                    "reasoning": content,
                    "severity": "medium",
                    "priority": 3
                }
                
        except Exception as e:
            logger.error(f"AWS Bedrock analysis failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is properly configured"""
        try:
            client = self._get_bedrock_client()
            return True
        except Exception:
            return False

class GoogleVertexProvider(AIProvider):
    """Google Vertex AI Claude implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._vertex_client = None
        
    def _get_vertex_client(self):
        """Initialize Vertex AI client lazily"""
        if self._vertex_client is None:
            try:
                from anthropic import AnthropicVertex
                self._vertex_client = AnthropicVertex(
                    project_id=self.config.get('project_id'),
                    region=self.config.get('location', 'us-central1')
                )
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}")
                raise
        return self._vertex_client
    
    async def analyze_security_event(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Analyze security event using Google Vertex AI Claude"""
        try:
            client = self._get_vertex_client()
            
            system_prompt = """You are a cybersecurity expert analyzing security events and determining appropriate response actions.

Available MCP servers and their capabilities:
1. VirusTotal (virustotal): IP reputation, domain reputation, file analysis
2. ServiceNow (servicenow): Create incidents, manage tickets, track responses
3. CyberReason (cyberreason): Endpoint investigation, threat hunting, host analysis
4. Custom REST (custom_rest): Generic API integration for custom threat intelligence

Analyze the security event and user prompt to determine:
1. What actions should be taken
2. Which MCP servers to use
3. Priority and severity assessment
4. Detailed reasoning for decisions

Return a JSON response with:
- actions: List of recommended actions with server and parameters
- reasoning: Explanation of decision process
- severity: Event severity (low/medium/high/critical)
- priority: Response priority (1-5)"""

            user_message = f"""Security Event Data:
{json.dumps(event_data, indent=2)}

User Prompt: {user_prompt}

Please analyze this security event and provide recommendations."""

            response = client.messages.create(
                model=self.config.get('model', 'claude-3-5-sonnet@20241022'),
                max_tokens=self.config.get('max_tokens', 2000),
                temperature=self.config.get('temperature', 0.1),
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            content = response.content[0].text
            
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, wrap in a basic structure
                return {
                    "actions": [],
                    "reasoning": content,
                    "severity": "medium",
                    "priority": 3
                }
                
        except Exception as e:
            logger.error(f"Google Vertex AI analysis failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Google Vertex AI is properly configured"""
        try:
            client = self._get_vertex_client()
            return True
        except Exception:
            return False

class AIProviderFactory:
    """Factory for creating AI providers"""
    
    _providers = {
        "aws_bedrock": AWSBedrockProvider,
        "google_vertex": GoogleVertexProvider
    }
    
    @classmethod
    def create_provider(cls, ai_config: Dict[str, Any]) -> AIProvider:
        """Create an AI provider based on configuration"""
        provider_type = ai_config.get("provider", "aws_bedrock")
        
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown AI provider: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        provider_config = ai_config.get(provider_type, {})
        
        return provider_class(provider_config)
    
    @classmethod
    def get_available_providers(cls, ai_config: Dict[str, Any]) -> list:
        """Get list of available and properly configured providers"""
        available = []
        
        for provider_type in cls._providers:
            try:
                provider_config = ai_config.get(provider_type, {})
                provider = cls._providers[provider_type](provider_config)
                if provider.is_available():
                    available.append(provider_type)
            except Exception:
                continue
                
        return available

class RuleBasedFallback:
    """Fallback rule-based analysis when AI providers are unavailable"""
    
    @staticmethod
    def analyze_security_event(event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Basic rule-based analysis as fallback"""
        actions = []
        severity = "medium"
        priority = 3
        
        # Extract potential IOCs
        event_str = json.dumps(event_data).lower()
        user_prompt_lower = user_prompt.lower()
        
        # Check for IP addresses or domains for VirusTotal lookup
        if any(field in event_data for field in ['ip', 'domain', 'src_ip', 'dst_ip']):
            if any(keyword in user_prompt_lower for keyword in ['malicious', 'reputation', 'check', 'analyze']):
                actions.append({
                    "server": "virustotal",
                    "action": "ip_report" if 'ip' in event_str else "domain_report",
                    "parameters": event_data
                })
        
        # Check for high severity events that need ServiceNow tickets
        if any(keyword in event_str for keyword in ['critical', 'high', 'malware', 'breach']):
            severity = "high"
            priority = 4
            if any(keyword in user_prompt_lower for keyword in ['ticket', 'incident', 'create']):
                actions.append({
                    "server": "servicenow",
                    "action": "create_record",
                    "parameters": {
                        "type": "incident",
                        "summary": f"Security Event: {event_data.get('event_type', 'Unknown')}",
                        "description": json.dumps(event_data),
                        "priority": priority
                    }
                })
        
        # Check for host-related events for CyberReason
        if any(field in event_data for field in ['hostname', 'host', 'endpoint']):
            if any(keyword in user_prompt_lower for keyword in ['endpoint', 'host', 'investigate']):
                actions.append({
                    "server": "cyberreason",
                    "action": "get_pylum_id",
                    "parameters": {"hostname": event_data.get('hostname', event_data.get('host', ''))}
                })
        
        return {
            "actions": actions,
            "reasoning": f"Rule-based analysis: Identified {len(actions)} recommended actions based on event attributes and user prompt keywords.",
            "severity": severity,
            "priority": priority,
            "fallback_used": True
        }