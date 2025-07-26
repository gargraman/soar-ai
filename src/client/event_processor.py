
import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from .event_parser import EventParser, SecurityEventTaxonomy
from .ai_provider import AIProviderFactory, RuleBasedFallback
from ..config.settings import AppConfig

class EventProcessor:
    """AI-driven event processor supporting multiple AI providers"""
    
    def __init__(self, mcp_client, config: AppConfig = None):
        self.mcp_client = mcp_client
        self.config = config or AppConfig()
        self.event_parser = EventParser()
        
        # Initialize AI provider
        try:
            self.ai_provider = AIProviderFactory.create_provider(self.config.ai_config)
        except Exception as e:
            print(f"Failed to initialize AI provider: {e}")
            self.ai_provider = None
        
    async def process_event(self, event_data: Dict[str, Any], user_prompt: str, event_format: str = "auto") -> Dict[str, Any]:
        """Process a security event using Claude 3.5 Sonnet AI reasoning"""
        
        # Parse event using standardized taxonomy
        parsed_event = self.event_parser.parse_event(event_data, event_format)
        
        # Convert parsed event to dictionary for analysis
        event_attributes = parsed_event.to_dict()
        
        # Use AI provider to analyze event and prompt to determine actions
        analysis = await self.analyze_with_ai(event_data, event_attributes, user_prompt)
        
        # Execute determined actions
        results = await self.execute_actions(event_data, analysis)
        
        return {
            "event_id": parsed_event.event_id or event_data.get("id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "parsed_event": event_attributes,
            "analysis": analysis,
            "results": results,
            "user_prompt": user_prompt,
            "original_format": event_format
        }
        
    async def analyze_with_ai(self, event_data: Dict[str, Any], event_attributes: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Use configured AI provider to analyze event and determine actions"""
        
        try:
            if self.ai_provider and self.ai_provider.is_available():
                # Use configured AI provider
                analysis = await self.ai_provider.analyze_security_event(event_data, user_prompt)
                
                # Convert AI provider response to expected format
                return self.convert_ai_response_to_analysis(analysis, event_attributes)
            else:
                # Fallback to rule-based analysis
                print(f"AI provider not available, falling back to rule-based analysis")
                return self.fallback_analysis(event_attributes, user_prompt)
                
        except Exception as e:
            # Fallback to rule-based analysis if AI provider fails
            print(f"AI analysis failed: {e}, falling back to rule-based analysis")
            if self.config.ai_config.get("fallback_to_rules", True):
                return RuleBasedFallback.analyze_security_event(event_data, user_prompt)
            else:
                raise
    
    def convert_ai_response_to_analysis(self, ai_response: Dict[str, Any], event_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI provider response to expected analysis format"""
        # Map AI provider response to our expected format
        determined_actions = []
        
        for i, action in enumerate(ai_response.get("actions", []), 1):
            determined_actions.append({
                "step": i,
                "server": action.get("server", ""),
                "action": action.get("action", ""),
                "parameters": action.get("parameters", {}),
                "priority": action.get("priority", "medium"),
                "depends_on": action.get("depends_on"),
                "condition": action.get("condition"),
                "rationale": action.get("rationale", "")
            })
        
        return {
            "event_attributes": event_attributes,
            "determined_actions": determined_actions,
            "reasoning": ai_response.get("reasoning", ""),
            "flow_strategy": ai_response.get("flow_strategy", ""),
            "severity_assessment": ai_response.get("severity", "medium"),
            "risk_indicators": ai_response.get("risk_indicators", []),
            "expected_flow_outcomes": ai_response.get("expected_outcomes", []),
            "recommended_follow_up": ai_response.get("recommended_follow_up", ""),
            "ai_model": f"{self.config.ai_config.get('provider', 'unknown')}"
        }

    def build_claude_prompt(self, event_data: Dict[str, Any], event_attributes: Dict[str, Any], user_prompt: str) -> str:
        """Build a comprehensive prompt for Claude analysis (legacy method)"""
        
        prompt = f"""You are an expert cybersecurity analyst AI agent working with a Model Context Protocol (MCP) system. Your task is to analyze security events and determine which MCP servers to query based on the event data and user instructions. You can create sequential flows where one server's output feeds into another server's input.

Available MCP Servers and their capabilities:
1. VirusTotal Server:
   - ip_report: Get IP reputation and threat intelligence
   - domain_report: Get domain reputation and threat intelligence
   - file_report: Get file hash analysis results

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
   - osint_lookup: Open source intelligence gathering

Original Event Data:
{json.dumps(event_data, indent=2)}

Standardized Event Attributes (using Security Event Taxonomy):
{json.dumps(event_attributes, indent=2)}

User Prompt: "{user_prompt}"

IMPORTANT: You can create sequential flows where actions depend on previous results. Use the "depends_on" field to specify dependencies and the "condition" field to specify when an action should execute based on previous results.

Example sequential flow:
1. First: Check IP reputation via VirusTotal
2. Then: IF threat score > 70, create ServiceNow incident
3. Then: IF incident created, check endpoint status via CyberReason
4. Finally: Update ServiceNow incident with endpoint findings

Please analyze this security event and user prompt, then determine:
1. What actions should be taken based on the event content and user request
2. Which MCP servers should be queried and in what order
3. How outputs from one server should influence subsequent actions
4. The reasoning behind your flow orchestration decisions

Respond in the following JSON format:
{{
    "reasoning": "Your detailed analysis and reasoning about the sequential flow",
    "severity_assessment": "low|medium|high|critical",
    "flow_strategy": "Description of the overall flow strategy and server interaction approach",
    "determined_actions": [
        {{
            "step": 1,
            "server": "server_name",
            "action": "action_name",
            "parameters": {{"key": "value"}},
            "priority": "low|medium|high",
            "depends_on": null,
            "condition": null,
            "rationale": "Why this action is needed and why it's first"
        }},
        {{
            "step": 2,
            "server": "server_name",
            "action": "action_name",
            "parameters": {{"key": "value"}},
            "priority": "low|medium|high",
            "depends_on": 1,
            "condition": "threat_score > 70",
            "rationale": "Why this action depends on step 1 results"
        }}
    ],
    "risk_indicators": [
        "List of identified risk indicators"
    ],
    "expected_flow_outcomes": [
        "What you expect from each step in the flow"
    ],
    "recommended_follow_up": "Additional recommendations"
}}

Focus on:
- IOC (Indicators of Compromise) identification and enrichment
- Sequential threat analysis workflows
- Conditional logic based on threat intelligence results
- Comprehensive incident management flows
- Endpoint investigation cascades
- Context-aware server selection and ordering
- Dependencies between different security analysis steps
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
                
                # Sort actions by step number for proper sequential execution
                determined_actions = claude_analysis.get("determined_actions", [])
                if determined_actions:
                    determined_actions.sort(key=lambda x: x.get("step", 0))
                
                return {
                    "event_attributes": event_attributes,
                    "determined_actions": determined_actions,
                    "reasoning": claude_analysis.get("reasoning", ""),
                    "flow_strategy": claude_analysis.get("flow_strategy", ""),
                    "severity_assessment": claude_analysis.get("severity_assessment", "medium"),
                    "risk_indicators": claude_analysis.get("risk_indicators", []),
                    "expected_flow_outcomes": claude_analysis.get("expected_flow_outcomes", []),
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
                "flow_strategy": "Fallback to simple analysis",
                "severity_assessment": "medium",
                "risk_indicators": [],
                "expected_flow_outcomes": [],
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
        """Execute the determined actions via MCP servers in sequential order with dependency handling"""
        results = []
        action_results = {}  # Store results by step number for dependency resolution
        
        for action in analysis["determined_actions"]:
            step = action.get("step", len(results) + 1)
            
            # Check if this action depends on a previous step
            depends_on = action.get("depends_on")
            condition = action.get("condition")
            
            should_execute = True
            dependency_result = None
            
            if depends_on is not None:
                dependency_result = action_results.get(depends_on)
                if dependency_result is None:
                    should_execute = False
                    results.append({
                        "step": step,
                        "action": action,
                        "success": False,
                        "error": f"Dependency step {depends_on} not found or failed",
                        "timestamp": datetime.now().isoformat(),
                        "ai_reasoning": action.get("rationale", ""),
                        "skipped": True
                    })
                    continue
                
                # Evaluate condition if specified
                if condition and not self.evaluate_condition(condition, dependency_result):
                    should_execute = False
                    results.append({
                        "step": step,
                        "action": action,
                        "success": True,
                        "result": {"message": f"Condition '{condition}' not met, step skipped"},
                        "timestamp": datetime.now().isoformat(),
                        "ai_reasoning": action.get("rationale", ""),
                        "skipped": True,
                        "condition_evaluated": condition
                    })
                    continue
            
            if should_execute:
                try:
                    # Enhance parameters with dependency results if needed
                    enhanced_parameters = self.enhance_parameters_with_dependencies(
                        action["parameters"], dependency_result, action
                    )
                    
                    result = await self.mcp_client.call_server(
                        action["server"],
                        action["action"], 
                        enhanced_parameters
                    )
                    
                    action_result = {
                        "step": step,
                        "action": action,
                        "success": True,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                        "ai_reasoning": action.get("rationale", ""),
                        "dependency_used": depends_on is not None
                    }
                    
                    results.append(action_result)
                    action_results[step] = action_result
                    
                except Exception as e:
                    error_result = {
                        "step": step,
                        "action": action,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "ai_reasoning": action.get("rationale", ""),
                        "dependency_used": depends_on is not None
                    }
                    
                    results.append(error_result)
                    # Don't store failed results for dependencies
                
        return results
    
    def evaluate_condition(self, condition: str, dependency_result: Dict[str, Any]) -> bool:
        """Evaluate a condition based on dependency result"""
        try:
            if not dependency_result.get("success", False):
                return False
                
            result_data = dependency_result.get("result", {})
            
            # Common condition patterns
            if "threat_score" in condition:
                # Extract threat score from various possible locations
                threat_score = 0
                if "threat_score" in result_data:
                    threat_score = result_data["threat_score"]
                elif "data" in result_data and "threat_score" in result_data["data"]:
                    threat_score = result_data["data"]["threat_score"]
                elif "malicious" in result_data and "total" in result_data:
                    # VirusTotal-style response
                    malicious = result_data.get("malicious", 0)
                    total = result_data.get("total", 1)
                    threat_score = (malicious / total) * 100 if total > 0 else 0
                
                # Evaluate numeric conditions
                if ">" in condition:
                    threshold = float(condition.split(">")[1].strip())
                    return threat_score > threshold
                elif "<" in condition:
                    threshold = float(condition.split("<")[1].strip())
                    return threat_score < threshold
                elif "==" in condition:
                    threshold = float(condition.split("==")[1].strip())
                    return threat_score == threshold
            
            elif "severity" in condition:
                severity = result_data.get("severity", "").lower()
                if "high" in condition.lower():
                    return severity in ["high", "critical"]
                elif "critical" in condition.lower():
                    return severity == "critical"
                elif "medium" in condition.lower():
                    return severity in ["medium", "high", "critical"]
            
            elif "compromised" in condition.lower():
                status = result_data.get("status", "").lower()
                return "compromised" in status or "infected" in status
            
            elif "malicious" in condition.lower():
                return result_data.get("malicious", 0) > 0 or "malicious" in str(result_data).lower()
            
            return True  # Default to true if condition can't be evaluated
            
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def enhance_parameters_with_dependencies(self, parameters: Dict[str, Any], dependency_result: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance action parameters with data from dependency results"""
        if not dependency_result or not dependency_result.get("success"):
            return parameters
        
        enhanced_params = parameters.copy()
        result_data = dependency_result.get("result", {})
        
        # Auto-enhance ServiceNow incident creation with threat intelligence
        if action.get("server") == "servicenow" and action.get("action") == "create_record":
            if "description" in enhanced_params:
                # Append threat intelligence findings to description
                if "threat_score" in result_data:
                    enhanced_params["description"] += f"\n\nThreat Intelligence:\nThreat Score: {result_data['threat_score']}"
                if "malicious" in result_data and "total" in result_data:
                    enhanced_params["description"] += f"\nVirusTotal Detections: {result_data['malicious']}/{result_data['total']}"
                if "reputation" in result_data:
                    enhanced_params["description"] += f"\nReputation: {result_data['reputation']}"
            
            # Set priority based on threat level
            if "threat_score" in result_data:
                threat_score = result_data["threat_score"]
                if threat_score > 80:
                    enhanced_params["priority"] = "1 - Critical"
                elif threat_score > 60:
                    enhanced_params["priority"] = "2 - High"
                elif threat_score > 30:
                    enhanced_params["priority"] = "3 - Medium"
                else:
                    enhanced_params["priority"] = "4 - Low"
        
        # Auto-enhance incident updates with endpoint findings
        elif action.get("server") == "servicenow" and action.get("action") == "update_record":
            if "status" in result_data:
                enhanced_params["additional_comments"] = f"Endpoint Status: {result_data['status']}"
                if result_data.get("status") == "compromised":
                    enhanced_params["state"] = "In Progress"
                    enhanced_params["priority"] = "1 - Critical"
        
        return enhanced_params
