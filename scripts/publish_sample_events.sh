#!/bin/bash

# Publish Sample Security Events to Redpanda Topics
# This script demonstrates publishing messages to various topics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-soar-messaging"
BROKER_CONTAINER="redpanda-1"

echo -e "${BLUE}📤 Publishing Sample Security Events${NC}"
echo "===================================="

# Check if Redpanda cluster is running
if ! docker compose -p $PROJECT_NAME ps --format json | jq -r '.[] | select(.Service=="redpanda-1") | .State' | grep -q "running"; then
    echo -e "${RED}❌ Redpanda cluster is not running. Please start it first with: ./scripts/start_messaging_infra.sh${NC}"
    exit 1
fi

# Function to publish a message
publish_message() {
    local topic=$1
    local message=$2
    local description=$3
    
    echo -e "${YELLOW}📨 Publishing to topic: ${BLUE}$topic${NC}"
    echo "   Description: $description"
    
    if echo "$message" | docker exec -i $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic produce $topic; then
        echo -e "   ${GREEN}✅ Message published successfully${NC}"
    else
        echo -e "   ${RED}❌ Failed to publish message${NC}"
        return 1
    fi
    echo ""
}

# Sample security events
echo -e "${BLUE}Publishing sample security events...${NC}\n"

# Malware detection event
MALWARE_EVENT='{
  "id": "evt_malware_001",
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "malware_detection",
  "severity": "high",
  "source_ip": "192.168.1.100",
  "hostname": "workstation-01",
  "description": "Trojan detected on endpoint",
  "indicators": {
    "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
    "file_path": "/tmp/suspicious.exe",
    "malware_family": "Emotet"
  },
  "metadata": {
    "detector": "ClamAV",
    "confidence": 0.95
  }
}'

publish_message "malware-events" "$MALWARE_EVENT" "Malware detection on endpoint"

# Network anomaly event
NETWORK_EVENT='{
  "id": "evt_network_001", 
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "network_anomaly",
  "severity": "medium",
  "source_ip": "192.168.1.50",
  "destination_domain": "malicious-domain.com",
  "destination_ip": "203.0.113.10",
  "hostname": "server-02",
  "description": "Suspicious outbound connection detected",
  "indicators": {
    "bytes_transferred": 1048576,
    "connection_duration": 300,
    "protocol": "HTTPS"
  },
  "metadata": {
    "detector": "Suricata",
    "rule_id": "2001234"
  }
}'

publish_message "network-events" "$NETWORK_EVENT" "Suspicious network connection"

# Authentication failure event
AUTH_EVENT='{
  "id": "evt_auth_001",
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "failed_login",
  "severity": "medium",
  "source_ip": "203.0.113.45",
  "hostname": "web-server-01",
  "username": "admin",
  "description": "Multiple failed login attempts detected",
  "indicators": {
    "failed_attempts": 15,
    "time_window": "5 minutes",
    "user_agent": "Mozilla/5.0 (compatible; Baiduspider/2.0)"
  },
  "metadata": {
    "detector": "fail2ban",
    "blocked": true
  }
}'

publish_message "authentication-events" "$AUTH_EVENT" "Brute force login attempt"

# Endpoint security event
ENDPOINT_EVENT='{
  "id": "evt_endpoint_001",
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "privilege_escalation",
  "severity": "high",
  "hostname": "database-server-01",
  "username": "service_account",
  "description": "Unexpected privilege escalation detected",
  "indicators": {
    "process_name": "powershell.exe",
    "command_line": "powershell -enc <base64_encoded_command>",
    "parent_process": "winlogon.exe",
    "escalated_privileges": ["SeDebugPrivilege", "SeTcbPrivilege"]
  },
  "metadata": {
    "detector": "Sysmon",
    "event_id": 4672
  }
}'

publish_message "endpoint-events" "$ENDPOINT_EVENT" "Privilege escalation attempt"

# High priority consolidated event
HIGH_PRIORITY_EVENT='{
  "id": "evt_critical_001",
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "apt_activity",
  "severity": "critical",
  "source_ip": "192.168.1.200",
  "hostname": "domain-controller-01",
  "description": "Advanced Persistent Threat activity detected",
  "indicators": {
    "attack_stages": ["reconnaissance", "lateral_movement", "data_exfiltration"],
    "iocs": ["203.0.113.10", "malicious-domain.com", "d41d8cd98f00b204e9800998ecf8427e"],
    "affected_systems": ["workstation-01", "server-02", "database-server-01"]
  },
  "metadata": {
    "correlation_id": "corr_001",
    "analyst_assigned": "security_team_lead",
    "priority": 1
  }
}'

publish_message "high-priority-events" "$HIGH_PRIORITY_EVENT" "Critical APT activity"

# General security event
SECURITY_EVENT='{
  "id": "evt_general_001",
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "event_type": "data_exfiltration",
  "severity": "high",
  "source_ip": "192.168.1.150",
  "destination_ip": "198.51.100.10",
  "hostname": "file-server-01",
  "description": "Large data transfer to external IP",
  "indicators": {
    "bytes_transferred": 10737418240,
    "transfer_duration": 1800,
    "files_accessed": ["/sensitive/customer_data.db", "/sensitive/financial_records.xlsx"]
  },
  "metadata": {
    "detector": "DLP_System",
    "policy_violated": "Data_Exfiltration_Policy"
  }
}'

publish_message "security-events" "$SECURITY_EVENT" "Potential data exfiltration"

echo -e "${GREEN}✅ All sample events published successfully!${NC}"
echo "==========================================="
echo ""
echo -e "${BLUE}🖥️  View messages in Redpanda Console:${NC}"
echo "  • URL: http://localhost:8088"
echo "  • Go to Topics → [topic-name] → Messages"
echo ""
echo -e "${BLUE}📊 Command line consumers:${NC}"
echo "  • Consume from security-events:"
echo "    docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic consume security-events --print-headers"
echo ""
echo "  • Consume from high-priority-events:"
echo "    docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic consume high-priority-events --print-headers"
echo ""
echo -e "${GREEN}🎉 Ready to process security events!${NC}"