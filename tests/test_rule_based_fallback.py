import pytest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'client')))
from ai_provider import RuleBasedFallback

def test_virustotal_ip_report():
    event = {"ip": "8.8.8.8", "event_type": "network_alert"}
    prompt = "Check if this IP is malicious."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "virustotal" and a["action"] == "ip_report" for a in result["actions"])
    assert result["fallback_used"]

def test_virustotal_domain_report():
    event = {"domain": "example.com", "event_type": "dns_query"}
    prompt = "Analyze the reputation of this domain."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "virustotal" and a["action"] == "domain_report" for a in result["actions"])

def test_virustotal_file_report():
    event = {"sha256": "abc123", "event_type": "file_upload"}
    prompt = "Scan this file hash for threats."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "virustotal" and a["action"] == "file_report" for a in result["actions"])

def test_servicenow_incident():
    event = {"event_type": "malware_detected", "description": "Critical malware found", "severity": "critical"}
    prompt = "Create a ServiceNow ticket for this incident."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "servicenow" and a["action"] == "create_record" for a in result["actions"])
    assert result["severity"] == "high"
    assert result["priority"] == 4

def test_cyberreason_host_investigation():
    event = {"hostname": "host1", "event_type": "endpoint_alert"}
    prompt = "Investigate this endpoint in CyberReason."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "cyberreason" and a["action"] == "get_pylum_id" for a in result["actions"])

def test_custom_rest_enrich():
    event = {"event_type": "unknown_event", "data": "test"}
    prompt = "Enrich this event using custom REST API."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert any(a["server"] == "custom_rest" and a["action"] == "enrich_event" for a in result["actions"])

def test_no_action():
    event = {"event_type": "info", "message": "All good."}
    prompt = "Just log this event."
    result = RuleBasedFallback.analyze_security_event(event, prompt)
    assert result["actions"] == []
    assert result["severity"] == "medium"
    assert result["priority"] == 3
