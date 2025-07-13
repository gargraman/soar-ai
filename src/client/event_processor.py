
import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class EventProcessor:
    """AI-driven event processor that determines which MCP servers to query"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        
    async def process_event(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Process a security event using AI reasoning"""
        
        # Analyze event and prompt to determine actions
        analysis = self.analyze_event_and_prompt(event_data, user_prompt)
        
        # Execute determined actions
        results = await self.execute_actions(event_data, analysis)
        
        return {
            "event_id": event_data.get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "results": results,
            "user_prompt": user_prompt
        }
        
    def analyze_event_and_prompt(self, event_data: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Analyze event and user prompt to determine actions"""
        
        # Extract relevant attributes from event
        event_attributes = self.extract_event_attributes(event_data)
        
        # Determine actions based on prompt analysis
        actions = self.determine_actions(event_attributes, user_prompt)
        
        return {
            "event_attributes": event_attributes,
            "determined_actions": actions,
            "reasoning": self.generate_reasoning(event_attributes, user_prompt, actions)
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
        # Filter out obvious non-domains
        domains = [d for d in domains if '.' in d and not d.replace('.', '').isdigit()]
        if domains:
            attributes["indicators"]["domains"] = list(set(domains))
            
        # Extract common security event fields
        security_fields = {
            "severity": ["severity", "priority", "risk_level", "threat_level"],
            "host_info": ["hostname", "host", "computer_name", "endpoint"],
            "event_type": ["event_type", "alert_type", "detection_type", "rule_name"]
        }
        
        for attr_key, field_names in security_fields.items():
            for field in field_names:
                if field in event_data:
                    if attr_key == "host_info":
                        attributes[attr_key]["hostname"] = event_data[field]
                    else:
                        attributes[attr_key] = event_data[field]
                    break
                    
        return attributes
        
    def determine_actions(self, event_attributes: Dict[str, Any], user_prompt: str) -> List[Dict[str, Any]]:
        """Determine which MCP servers to query based on event and prompt"""
        actions = []
        prompt_lower = user_prompt.lower()
        
        # Check for VirusTotal actions
        if any(keyword in prompt_lower for keyword in ["malicious", "reputation", "scan", "virus", "threat"]):
            if "ips" in event_attributes.get("indicators", {}):
                for ip in event_attributes["indicators"]["ips"]:
                    actions.append({
                        "server": "virustotal",
                        "action": "ip_report",
                        "parameters": {"ip": ip}
                    })
                    
            if "domains" in event_attributes.get("indicators", {}):
                for domain in event_attributes["indicators"]["domains"]:
                    actions.append({
                        "server": "virustotal",
                        "action": "domain_report", 
                        "parameters": {"domain": domain}
                    })
                    
        # Check for ServiceNow actions
        if any(keyword in prompt_lower for keyword in ["ticket", "incident", "servicenow", "create", "alert"]):
            severity = event_attributes.get("severity", "medium")
            if any(keyword in prompt_lower for keyword in ["high", "critical"]) or severity in ["high", "critical"]:
                actions.append({
                    "server": "servicenow",
                    "action": "create_record",
                    "parameters": {
                        "type": "incident",
                        "summary": f"Security event detected: {event_attributes.get('event_type', 'Unknown')}",
                        "description": json.dumps(event_attributes, indent=2),
                        "severity": severity
                    }
                })
                
        # Check for CyberReason actions
        if any(keyword in prompt_lower for keyword in ["endpoint", "terminal", "host", "pylum", "cyberreason"]):
            hostname = event_attributes.get("host_info", {}).get("hostname")
            if hostname:
                actions.append({
                    "server": "cyberreason", 
                    "action": "get_pylum_id",
                    "parameters": {"hostname": hostname}
                })
                actions.append({
                    "server": "cyberreason",
                    "action": "check_terminal_status", 
                    "parameters": {"hostname": hostname}
                })
                
        # Fallback logic - if no specific actions determined, do basic enrichment
        if not actions:
            if "ips" in event_attributes.get("indicators", {}):
                for ip in event_attributes["indicators"]["ips"][:3]:  # Limit to first 3 IPs
                    actions.append({
                        "server": "virustotal",
                        "action": "ip_report",
                        "parameters": {"ip": ip}
                    })
                    
        return actions
        
    def generate_reasoning(self, event_attributes: Dict[str, Any], user_prompt: str, actions: List[Dict[str, Any]]) -> str:
        """Generate human-readable reasoning for the determined actions"""
        reasoning = f"Analysis of user prompt: '{user_prompt}'\n"
        reasoning += f"Event contains: {list(event_attributes.get('indicators', {}).keys())}\n"
        reasoning += f"Determined {len(actions)} actions:\n"
        
        for i, action in enumerate(actions, 1):
            reasoning += f"  {i}. Query {action['server']} for {action['action']} with {action['parameters']}\n"
            
        return reasoning
        
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
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
        return results
