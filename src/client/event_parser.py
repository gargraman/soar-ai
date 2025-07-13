
import json
import re
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

@dataclass
class SecurityEventTaxonomy:
    """Standardized field taxonomy for security events"""
    
    # Core event identifiers
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    
    # Network information
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    
    # Host information
    hostname: Optional[str] = None
    computer_name: Optional[str] = None
    domain: Optional[str] = None
    operating_system: Optional[str] = None
    
    # User information
    username: Optional[str] = None
    user_id: Optional[str] = None
    user_domain: Optional[str] = None
    
    # Process information
    process_name: Optional[str] = None
    process_id: Optional[int] = None
    parent_process_name: Optional[str] = None
    parent_process_id: Optional[int] = None
    command_line: Optional[str] = None
    
    # File information
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_hash_md5: Optional[str] = None
    file_hash_sha1: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    file_size: Optional[int] = None
    
    # Detection information
    rule_name: Optional[str] = None
    rule_id: Optional[str] = None
    detection_engine: Optional[str] = None
    signature_id: Optional[str] = None
    
    # Additional context
    description: Optional[str] = None
    raw_event: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

class EventParser:
    """Parser for different security event formats with field taxonomy mapping"""
    
    def __init__(self):
        self.field_mappings = self._initialize_field_mappings()
        
    def _initialize_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize field mappings for different log sources"""
        return {
            "windows_eventlog": {
                "EventID": "event_id",
                "TimeCreated": "timestamp",
                "Computer": "hostname",
                "SubjectUserName": "username",
                "SubjectDomainName": "user_domain",
                "ProcessName": "process_name",
                "ProcessId": "process_id",
                "IpAddress": "source_ip",
                "IpPort": "source_port"
            },
            "syslog": {
                "timestamp": "timestamp",
                "hostname": "hostname",
                "program": "process_name",
                "pid": "process_id",
                "message": "description",
                "severity": "severity",
                "facility": "detection_engine"
            },
            "cisco_asa": {
                "timestamp": "timestamp",
                "src": "source_ip",
                "dst": "destination_ip",
                "sport": "source_port",
                "dport": "destination_port",
                "proto": "protocol",
                "action": "event_type"
            },
            "palo_alto": {
                "time_generated": "timestamp",
                "src": "source_ip",
                "dst": "destination_ip",
                "sport": "source_port",
                "dport": "destination_port",
                "proto": "protocol",
                "action": "event_type",
                "threat": "rule_name"
            },
            "crowdstrike": {
                "timestamp": "timestamp",
                "ComputerName": "hostname",
                "UserName": "username",
                "FileName": "file_name",
                "FilePath": "file_path",
                "MD5String": "file_hash_md5",
                "SHA256String": "file_hash_sha256",
                "ProcessDisplayName": "process_name",
                "ParentProcessId": "parent_process_id"
            },
            "splunk_cim": {
                "_time": "timestamp",
                "dest": "hostname",
                "src": "source_ip",
                "dest_ip": "destination_ip",
                "src_port": "source_port",
                "dest_port": "destination_port",
                "user": "username",
                "signature": "rule_name",
                "severity": "severity"
            }
        }
    
    def parse_event(self, event_data: Union[str, Dict[str, Any]], format_type: str = "auto") -> SecurityEventTaxonomy:
        """Parse security event from various formats"""
        
        if format_type == "auto":
            format_type = self._detect_format(event_data)
        
        if format_type == "json":
            return self._parse_json_event(event_data)
        elif format_type == "syslog":
            return self._parse_syslog_event(event_data)
        elif format_type == "csv":
            return self._parse_csv_event(event_data)
        else:
            # Try to parse as generic JSON
            return self._parse_generic_event(event_data)
    
    def _detect_format(self, event_data: Union[str, Dict[str, Any]]) -> str:
        """Auto-detect event format"""
        
        if isinstance(event_data, dict):
            return "json"
        
        if isinstance(event_data, str):
            # Try to parse as JSON first
            try:
                json.loads(event_data)
                return "json"
            except:
                pass
            
            # Check for syslog patterns
            syslog_patterns = [
                r'<\d+>',  # Priority
                r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Timestamp
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'  # ISO timestamp
            ]
            
            if any(re.search(pattern, event_data) for pattern in syslog_patterns):
                return "syslog"
            
            # Check for CSV format
            if ',' in event_data and not '{' in event_data:
                return "csv"
        
        return "generic"
    
    def _parse_json_event(self, event_data: Union[str, Dict[str, Any]]) -> SecurityEventTaxonomy:
        """Parse JSON format event"""
        
        if isinstance(event_data, str):
            try:
                data = json.loads(event_data)
            except:
                return SecurityEventTaxonomy(raw_event=event_data)
        else:
            data = event_data
        
        return self._map_fields_to_taxonomy(data)
    
    def _parse_syslog_event(self, event_data: str) -> SecurityEventTaxonomy:
        """Parse syslog format event"""
        
        syslog_data = {}
        
        # Parse RFC3164 syslog format
        rfc3164_pattern = r'<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s*(.*)'
        match = re.match(rfc3164_pattern, event_data)
        
        if match:
            priority, timestamp, hostname, program, pid, message = match.groups()
            
            # Calculate facility and severity from priority
            priority_int = int(priority)
            facility = priority_int // 8
            severity = priority_int % 8
            
            syslog_data = {
                "priority": priority_int,
                "facility": facility,
                "severity": self._map_syslog_severity(severity),
                "timestamp": timestamp,
                "hostname": hostname,
                "program": program,
                "pid": int(pid) if pid else None,
                "message": message
            }
        else:
            # Try RFC5424 format
            rfc5424_pattern = r'<(\d+)>(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)'
            match = re.match(rfc5424_pattern, event_data)
            
            if match:
                priority, version, timestamp, hostname, app_name, proc_id, msg_id, message = match.groups()
                
                priority_int = int(priority)
                facility = priority_int // 8
                severity = priority_int % 8
                
                syslog_data = {
                    "priority": priority_int,
                    "version": version,
                    "facility": facility,
                    "severity": self._map_syslog_severity(severity),
                    "timestamp": timestamp,
                    "hostname": hostname,
                    "app_name": app_name,
                    "proc_id": proc_id,
                    "msg_id": msg_id,
                    "message": message
                }
        
        if not syslog_data:
            # Fallback: treat entire line as message
            syslog_data = {"message": event_data, "raw_event": event_data}
        
        return self._map_fields_to_taxonomy(syslog_data, "syslog")
    
    def _parse_csv_event(self, event_data: str) -> SecurityEventTaxonomy:
        """Parse CSV format event (single row)"""
        
        # This would typically be used with a header row to map fields
        # For now, treat as raw data
        return SecurityEventTaxonomy(raw_event=event_data, description=event_data)
    
    def _parse_generic_event(self, event_data: Union[str, Dict[str, Any]]) -> SecurityEventTaxonomy:
        """Parse generic/unknown format event"""
        
        if isinstance(event_data, dict):
            return self._map_fields_to_taxonomy(event_data)
        else:
            return SecurityEventTaxonomy(raw_event=str(event_data), description=str(event_data))
    
    def _map_fields_to_taxonomy(self, data: Dict[str, Any], source_type: str = "generic") -> SecurityEventTaxonomy:
        """Map raw fields to standardized taxonomy"""
        
        taxonomy = SecurityEventTaxonomy()
        
        # Get appropriate field mapping
        field_mapping = self.field_mappings.get(source_type, {})
        
        # Direct field mapping
        for raw_field, taxonomy_field in field_mapping.items():
            if raw_field in data and hasattr(taxonomy, taxonomy_field):
                setattr(taxonomy, taxonomy_field, data[raw_field])
        
        # Generic field mapping (try common field names)
        self._apply_generic_mapping(taxonomy, data)
        
        # Extract additional fields that don't fit standard taxonomy
        self._extract_additional_fields(taxonomy, data)
        
        # Store raw event for reference
        taxonomy.raw_event = json.dumps(data) if isinstance(data, dict) else str(data)
        
        return taxonomy
    
    def _apply_generic_mapping(self, taxonomy: SecurityEventTaxonomy, data: Dict[str, Any]):
        """Apply generic field mappings for common field names"""
        
        generic_mappings = {
            # Event identifiers
            "event_id": ["id", "event_id", "eventid", "evt_id", "record_id"],
            "timestamp": ["timestamp", "time", "@timestamp", "event_time", "log_time", "created"],
            "event_type": ["event_type", "type", "category", "alert_type", "event_category"],
            "severity": ["severity", "level", "priority", "criticality", "risk_level"],
            
            # Network
            "source_ip": ["src_ip", "source_ip", "src", "source_address", "client_ip"],
            "destination_ip": ["dst_ip", "dest_ip", "destination_ip", "dst", "target_ip", "server_ip"],
            "source_port": ["src_port", "source_port", "sport", "client_port"],
            "destination_port": ["dst_port", "dest_port", "destination_port", "dport", "server_port"],
            "protocol": ["protocol", "proto", "ip_protocol"],
            
            # Host
            "hostname": ["hostname", "host", "computer", "computer_name", "machine_name", "endpoint"],
            "domain": ["domain", "dns_domain", "computer_domain"],
            "operating_system": ["os", "operating_system", "platform"],
            
            # User
            "username": ["user", "username", "account", "userid", "subject_user_name"],
            "user_domain": ["user_domain", "domain", "subject_domain_name"],
            
            # Process
            "process_name": ["process", "process_name", "image", "executable"],
            "process_id": ["pid", "process_id", "process_guid"],
            "command_line": ["command_line", "cmdline", "command"],
            
            # File
            "file_path": ["file_path", "path", "full_path", "target_filename"],
            "file_name": ["file_name", "filename", "name"],
            "file_hash_md5": ["md5", "file_hash", "hash_md5", "md5_hash"],
            "file_hash_sha1": ["sha1", "sha1_hash", "hash_sha1"],
            "file_hash_sha256": ["sha256", "sha256_hash", "hash_sha256"],
            "file_size": ["file_size", "size"],
            
            # Detection
            "rule_name": ["rule", "rule_name", "signature", "alert_name", "detection_name"],
            "rule_id": ["rule_id", "signature_id", "alert_id"],
            "detection_engine": ["engine", "detector", "source", "vendor", "product"],
            
            # Description
            "description": ["description", "message", "details", "summary", "reason"]
        }
        
        for taxonomy_field, possible_names in generic_mappings.items():
            if getattr(taxonomy, taxonomy_field) is None:  # Only if not already set
                for field_name in possible_names:
                    if field_name in data:
                        setattr(taxonomy, taxonomy_field, data[field_name])
                        break
    
    def _extract_additional_fields(self, taxonomy: SecurityEventTaxonomy, data: Dict[str, Any]):
        """Extract additional fields and create tags"""
        
        tags = []
        
        # Look for hash patterns in any field
        hash_patterns = {
            "md5": r'\b[a-fA-F0-9]{32}\b',
            "sha1": r'\b[a-fA-F0-9]{40}\b',
            "sha256": r'\b[a-fA-F0-9]{64}\b'
        }
        
        text_content = json.dumps(data).lower()
        
        for hash_type, pattern in hash_patterns.items():
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches and not getattr(taxonomy, f"file_hash_{hash_type}"):
                setattr(taxonomy, f"file_hash_{hash_type}", matches[0])
                tags.append(f"contains_{hash_type}_hash")
        
        # Extract IP addresses if not already found
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text_content)
        if ips:
            if not taxonomy.source_ip:
                taxonomy.source_ip = ips[0]
            if len(ips) > 1 and not taxonomy.destination_ip:
                taxonomy.destination_ip = ips[1]
            tags.append("contains_ip_addresses")
        
        # Add tags based on content
        threat_indicators = ["malware", "virus", "trojan", "ransomware", "phishing", "suspicious"]
        for indicator in threat_indicators:
            if indicator in text_content:
                tags.append(f"threat_{indicator}")
        
        if tags:
            taxonomy.tags = tags
    
    def _map_syslog_severity(self, severity_code: int) -> str:
        """Map syslog severity code to text"""
        severity_map = {
            0: "emergency",
            1: "alert", 
            2: "critical",
            3: "error",
            4: "warning",
            5: "notice",
            6: "info",
            7: "debug"
        }
        return severity_map.get(severity_code, "unknown")
    
    def parse_batch_events(self, events_data: List[Union[str, Dict[str, Any]]], format_type: str = "auto") -> List[SecurityEventTaxonomy]:
        """Parse multiple events"""
        
        parsed_events = []
        for event_data in events_data:
            try:
                parsed_event = self.parse_event(event_data, format_type)
                parsed_events.append(parsed_event)
            except Exception as e:
                # Create a basic event with error information
                error_event = SecurityEventTaxonomy(
                    description=f"Parse error: {str(e)}",
                    raw_event=str(event_data),
                    tags=["parse_error"]
                )
                parsed_events.append(error_event)
        
        return parsed_events
