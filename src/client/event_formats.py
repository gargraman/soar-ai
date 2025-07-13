
from typing import Dict, List, Any, Optional
import json
import re

class EventFormatExamples:
    """Examples and validators for different security event formats"""
    
    @staticmethod
    def get_json_examples() -> Dict[str, Dict[str, Any]]:
        """Get example JSON format events"""
        return {
            "crowdstrike_detection": {
                "event_id": "det_12345",
                "timestamp": "2024-01-20T10:30:00Z",
                "ComputerName": "LAPTOP-001",
                "UserName": "john.doe",
                "FileName": "malicious.exe",
                "FilePath": "C:\\Users\\john.doe\\Downloads\\malicious.exe",
                "MD5String": "d41d8cd98f00b204e9800998ecf8427e",
                "SHA256String": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "ProcessDisplayName": "malicious.exe",
                "DetectDescription": "Malware detected and quarantined",
                "Severity": "High"
            },
            "windows_eventlog": {
                "EventID": 4624,
                "TimeCreated": "2024-01-20T10:30:00Z",
                "Computer": "DC-001",
                "Channel": "Security",
                "SubjectUserName": "admin",
                "SubjectDomainName": "COMPANY",
                "IpAddress": "192.168.1.100",
                "LogonType": 3,
                "ProcessName": "winlogon.exe"
            },
            "generic_alert": {
                "id": "alert_001",
                "timestamp": "2024-01-20T10:30:00Z",
                "event_type": "network_intrusion",
                "severity": "high",
                "source_ip": "203.0.113.45",
                "destination_ip": "192.168.1.100",
                "rule_name": "Suspicious Network Activity",
                "description": "Potential data exfiltration detected"
            }
        }
    
    @staticmethod
    def get_syslog_examples() -> Dict[str, str]:
        """Get example Syslog format events"""
        return {
            "cisco_asa": "<166>Jan 20 10:30:00 firewall.company.com %ASA-6-302013: Built outbound TCP connection 12345 for outside:203.0.113.45/443 (203.0.113.45/443) to inside:192.168.1.100/54321",
            
            "palo_alto": "<14>Jan 20 10:30:00 PA-VM threat: 2024/01/20 10:30:00,001801000116,THREAT,url,2560,2024/01/20 10:30:00,192.168.1.100,203.0.113.45,0.0.0.0,0.0.0.0,rule1,johndoe,,web-browsing,vsys1,trust,untrust,ethernet1/1,ethernet1/2,forwarder,2024/01/20 10:30:00,12345,1,54321,443,0,0,0x400000,tcp,block,malicious-domain.com",
            
            "linux_auth": "<38>Jan 20 10:30:00 server-01 sshd[12345]: Failed password for invalid user admin from 203.0.113.45 port 54321 ssh2",
            
            "windows_syslog": "<134>Jan 20 10:30:00 DC-001 Microsoft-Windows-Security-Auditing: An account was successfully logged on. Subject: Security ID: S-1-5-21-1234567890-1234567890-1234567890-1000 Account Name: john.doe Account Domain: COMPANY",
            
            "rfc5424": "<165>1 2024-01-20T10:30:00.123Z firewall.company.com asa - - [origin@32473 ip=\"192.168.1.100\"] Built outbound connection"
        }
    
    @staticmethod
    def get_csv_examples() -> Dict[str, str]:
        """Get example CSV format events"""
        return {
            "splunk_export": "timestamp,src_ip,dest_ip,action,rule_name,severity\n2024-01-20T10:30:00Z,192.168.1.100,203.0.113.45,block,Suspicious Traffic,high",
            
            "firewall_log": "date,time,source,destination,protocol,port,action\n2024-01-20,10:30:00,192.168.1.100,203.0.113.45,TCP,443,DENY",
            
            "antivirus_log": "timestamp,computer,user,threat_name,file_path,action_taken\n2024-01-20 10:30:00,LAPTOP-001,john.doe,Trojan.Win32.Generic,C:\\temp\\malware.exe,Quarantined"
        }

class EventFormatValidator:
    """Validator for different event formats"""
    
    @staticmethod
    def validate_json_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize JSON event"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "normalized_event": event_data.copy()
        }
        
        # Check for required fields
        required_fields = ["timestamp"]
        for field in required_fields:
            if not any(key.lower().replace("_", "").replace(" ", "") == field for key in event_data.keys()):
                validation_result["warnings"].append(f"Missing recommended field: {field}")
        
        # Validate timestamp formats
        timestamp_fields = ["timestamp", "time", "@timestamp", "event_time", "TimeCreated"]
        for field in timestamp_fields:
            if field in event_data:
                if not EventFormatValidator._validate_timestamp(event_data[field]):
                    validation_result["warnings"].append(f"Invalid timestamp format in field: {field}")
        
        # Validate IP addresses
        ip_fields = ["source_ip", "destination_ip", "src_ip", "dst_ip", "IpAddress"]
        for field in ip_fields:
            if field in event_data:
                if not EventFormatValidator._validate_ip_address(str(event_data[field])):
                    validation_result["warnings"].append(f"Invalid IP address in field: {field}")
        
        return validation_result
    
    @staticmethod
    def validate_syslog_event(event_data: str) -> Dict[str, Any]:
        """Validate syslog event format"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "format": "unknown"
        }
        
        # Check for RFC3164 format
        rfc3164_pattern = r'<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)'
        if re.match(rfc3164_pattern, event_data):
            validation_result["format"] = "RFC3164"
            return validation_result
        
        # Check for RFC5424 format
        rfc5424_pattern = r'<(\d+)>(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)'
        if re.match(rfc5424_pattern, event_data):
            validation_result["format"] = "RFC5424"
            return validation_result
        
        # Check for basic syslog elements
        if not re.search(r'<\d+>', event_data):
            validation_result["warnings"].append("Missing priority field")
        
        if not re.search(r'\d{2}:\d{2}:\d{2}', event_data):
            validation_result["warnings"].append("Missing or invalid timestamp")
        
        validation_result["format"] = "non_standard"
        return validation_result
    
    @staticmethod
    def _validate_timestamp(timestamp_str: str) -> bool:
        """Validate timestamp format"""
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?',  # ISO 8601
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # Standard datetime
            r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Syslog format
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}'   # US format
        ]
        
        return any(re.match(pattern, str(timestamp_str)) for pattern in timestamp_patterns)
    
    @staticmethod
    def _validate_ip_address(ip_str: str) -> bool:
        """Validate IP address format"""
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        return bool(re.match(ipv4_pattern, ip_str) or re.match(ipv6_pattern, ip_str))
