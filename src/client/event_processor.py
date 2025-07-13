
import asyncio
import json
import re
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime

class EventProcessor:
    """AI-driven event processor using Claude 3.5 Sonnet from AWS Bedrock"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name='us-east-1'  # Claude is available in us-east-1
        )
        self.claude_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        
    async def process_event(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Process a security event using Claude 3.5 Sonnet AI reasoning"""
        
        # Extract event attributes first
        event_attributes = self.extract_event_attributes(event_data)
        
        # Use Claude to analyze event and prompt to determine actions
        analysis = await self.analyze_with_claude(event_data, event_attributes, user_prompt)
        
        # Execute determined actions
        results = await self.execute_actions(event_data, analysis)
        
        return {
            "event_id": event_data.get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "results": results,
            "user_prompt": user_prompt
        }
        
    async def analyze_with_claude(self, event_data: Dict[str, Any], event_attributes: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Use Claude 3.5 Sonnet to analyze event and determine actions"""
        
        # Prepare the prompt for Claude
        claude_prompt = self.build_claude_prompt(event_data, event_attributes, user_prompt)
        
        try:
            # Call Claude via AWS Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": claude_prompt
                        }
                    ]
                })
            )
            
            # Parse Claude's response
            response_body = json.loads(response['body'].read())
            claude_analysis = response_body['content'][0]['text']
            
            # Parse Claude's structured response
            analysis = self.parse_claude_response(claude_analysis, event_attributes)
            
            return analysis
            
        except Exception as e:
            # Fallback to rule-based analysis if Claude fails
            print(f"Claude analysis failed: {e}, falling back to rule-based analysis")
            return self.fallback_analysis(event_attributes, user_prompt)
    
    def build_claude_prompt(self, event_data: Dict[str, Any], event_attributes: Dict[str, Any], user_prompt: str) -> str:
        """Build a comprehensive prompt for Claude analysis"""
        
        prompt = f"""You are an expert cybersecurity analyst AI agent working with a Model Context Protocol (MCP) system. Your task is to analyze security events and determine which MCP servers to query based on the event data and user instructions.

Available MCP Servers and their capabilities:
1. VirusTotal Server:
   - ip_report: Get IP reputation and threat intelligence
   - domain_report: Get domain reputation and threat intelligence

2. ServiceNow Server:
   - create_record: Create incident tickets for security events
   - get_record: Retrieve existing incident information
   - update_record: Update existing incidents

3. CyberReason Server:
   - get_pylum_id: Get Pylum ID for hostname/endpoint identification
   - check_terminal_status: Check if terminal/endpoint is compromised
   - get_malops: Get malware operations data

4. Custom REST Server:
   - custom_enrichment: Call custom threat intelligence APIs
   - dynamic_api_calls: Make calls to registered third-party APIs

Security Event Data:
{json.dumps(event_data, indent=2)}

Extracted Event Attributes:
{json.dumps(event_attributes, indent=2)}

User Prompt: "{user_prompt}"

Please analyze this security event and user prompt, then determine:
1. What actions should be taken based on the event content and user request
2. Which MCP servers should be queried and with what parameters
3. The reasoning behind your decisions
4. Priority/severity assessment

Respond in the following JSON format:
{{
    "reasoning": "Your detailed analysis and reasoning",
    "severity_assessment": "low|medium|high|critical",
    "determined_actions": [
        {{
            "server": "server_name",
            "action": "action_name",
            "parameters": {{"key": "value"}},
            "priority": "low|medium|high",
            "rationale": "Why this action is needed"
        }}
    ],
    "risk_indicators": [
        "List of identified risk indicators"
    ],
    "recommended_follow_up": "Additional recommendations"
}}

Focus on:
- IOC (Indicators of Compromise) identification and enrichment
- Threat severity assessment
- Appropriate incident management
- Endpoint security analysis when hostnames are present
- Contextual understanding of the user's intent
"""
        return prompt
    
    def parse_claude_response(self, claude_response: str, event_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude's structured JSON response"""
        try:
            # Extract JSON from Claude's response
            json_start = claude_response.find('{')
            json_end = claude_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = claude_response[json_start:json_end]
                claude_analysis = json.loads(json_str)
                
                return {
                    "event_attributes": event_attributes,
                    "determined_actions": claude_analysis.get("determined_actions", []),
                    "reasoning": claude_analysis.get("reasoning", ""),
                    "severity_assessment": claude_analysis.get("severity_assessment", "medium"),
                    "risk_indicators": claude_analysis.get("risk_indicators", []),
                    "recommended_follow_up": claude_analysis.get("recommended_follow_up", ""),
                    "ai_model": "claude-3.5-sonnet"
                }
            else:
                raise ValueError("No valid JSON found in Claude response")
                
        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            # Return a basic analysis if parsing fails
            return {
                "event_attributes": event_attributes,
                "determined_actions": [],
                "reasoning": f"Claude response parsing failed: {str(e)}",
                "severity_assessment": "medium",
                "risk_indicators": [],
                "recommended_follow_up": "Manual review required",
                "ai_model": "claude-3.5-sonnet-fallback"
            }
    
    def fallback_analysis(self, event_attributes: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Fallback rule-based analysis if Claude is unavailable"""
        actions = []
        prompt_lower = user_prompt.lower()
        
        # Basic rule-based logic as fallback
        if any(keyword in prompt_lower for keyword in ["malicious", "reputation", "scan", "virus", "threat"]):
            if "ips" in event_attributes.get("indicators", {}):
                for ip in event_attributes["indicators"]["ips"][:3]:
                    actions.append({
                        "server": "virustotal",
                        "action": "ip_report",
                        "parameters": {"ip": ip},
                        "priority": "medium",
                        "rationale": "IP reputation check requested"
                    })
                    
        if any(keyword in prompt_lower for keyword in ["ticket", "incident", "servicenow"]):
            actions.append({
                "server": "servicenow",
                "action": "create_record",
                "parameters": {
                    "type": "incident",
                    "summary": f"Security event detected: {event_attributes.get('event_type', 'Unknown')}",
                    "description": json.dumps(event_attributes, indent=2),
                    "severity": event_attributes.get("severity", "medium")
                },
                "priority": "high",
                "rationale": "Incident creation requested"
            })
        
        return {
            "event_attributes": event_attributes,
            "determined_actions": actions,
            "reasoning": f"Fallback rule-based analysis for prompt: '{user_prompt}'",
            "severity_assessment": event_attributes.get("severity", "medium"),
            "risk_indicators": [],
            "recommended_follow_up": "Consider manual review",
            "ai_model": "rule-based-fallback"
        }
        
    def extract_event_attributes(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant security attributes from event data"""
        attributes = {
            "event_type": "unknown",
            "indicators": {},
            "severity": "unknown",
            "host_info": {},
            "network_info": {}
        }
        
        # Extract IPs
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        text_content = json.dumps(event_data)
        ips = re.findall(ip_pattern, text_content)
        if ips:
            attributes["indicators"]["ips"] = list(set(ips))
            
        # Extract domains
        domain_pattern = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\b'
        domains = re.findall(domain_pattern, text_content)
        domains = [d for d in domains if '.' in d and not d.replace('.', '').isdigit()]
        if domains:
            attributes["indicators"]["domains"] = list(set(domains))
            
        # Extract file hashes
        hash_patterns = {
            "md5": r'\b[a-fA-F0-9]{32}\b',
            "sha1": r'\b[a-fA-F0-9]{40}\b', 
            "sha256": r'\b[a-fA-F0-9]{64}\b'
        }
        
        for hash_type, pattern in hash_patterns.items():
            hashes = re.findall(pattern, text_content)
            if hashes:
                if "hashes" not in attributes["indicators"]:
                    attributes["indicators"]["hashes"] = {}
                attributes["indicators"][hash_type] = list(set(hashes))
        
        # Extract common security event fields
        security_fields = {
            "severity": ["severity", "priority", "risk_level", "threat_level", "criticality"],
            "host_info": ["hostname", "host", "computer_name", "endpoint", "machine_name"],
            "event_type": ["event_type", "alert_type", "detection_type", "rule_name", "category"],
            "network_info": ["src_ip", "dst_ip", "source_ip", "destination_ip", "protocol", "port"]
        }
        
        for attr_key, field_names in security_fields.items():
            for field in field_names:
                if field in event_data:
                    if attr_key == "host_info":
                        attributes[attr_key]["hostname"] = event_data[field]
                    elif attr_key == "network_info":
                        attributes[attr_key][field] = event_data[field]
                    else:
                        attributes[attr_key] = event_data[field]
                    break
                    
        return attributes
        
    async def execute_actions(self, event_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute the determined actions via MCP servers"""
        results = []
        
        for action in analysis["determined_actions"]:
            try:
                result = await self.mcp_client.call_server(
                    action["server"],
                    action["action"], 
                    action["parameters"]
                )
                
                results.append({
                    "action": action,
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "ai_reasoning": action.get("rationale", "")
                })
                
            except Exception as e:
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "ai_reasoning": action.get("rationale", "")
                })
                
        return results
