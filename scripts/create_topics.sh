#!/bin/bash

# Create Kafka Topics for AI-SOAR Platform
# This script creates all required topics for the cybersecurity automation platform

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

echo -e "${BLUE}📝 Creating Kafka Topics for AI-SOAR Platform${NC}"
echo "==============================================="

# Check if Redpanda cluster is running
if ! docker compose -p $PROJECT_NAME ps --format json | jq -r '.[] | select(.Service=="redpanda-1") | .State' | grep -q "running"; then
    echo -e "${RED}❌ Redpanda cluster is not running. Please start it first with: ./scripts/start_messaging_infra.sh${NC}"
    exit 1
fi

# Function to create a topic
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    local description=$4
    
    echo -e "${YELLOW}📂 Creating topic: ${BLUE}$topic_name${NC}"
    echo "   Partitions: $partitions, Replication Factor: $replication_factor"
    echo "   Description: $description"
    
    # Check if topic already exists
    if docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic list | grep -q "^$topic_name"; then
        echo -e "   ${YELLOW}⚠️  Topic already exists, skipping...${NC}"
    else
        # Create the topic
        if docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic create $topic_name \
            --partitions $partitions \
            --replicas $replication_factor \
            --config cleanup.policy=delete \
            --config retention.ms=604800000; then  # 7 days retention
            echo -e "   ${GREEN}✅ Created successfully${NC}"
        else
            echo -e "   ${RED}❌ Failed to create topic${NC}"
            return 1
        fi
    fi
    echo ""
}

# Create topics for different event types
echo -e "${BLUE}Creating security event topics...${NC}\n"

# Main security events topic
create_topic "security-events" 6 3 "Main topic for all security events from various sources"

# Event type specific topics
create_topic "malware-events" 3 3 "Malware detection and analysis events"
create_topic "network-events" 3 3 "Network anomalies and intrusion attempts"
create_topic "endpoint-events" 3 3 "Endpoint security and host-based events"
create_topic "authentication-events" 3 3 "Authentication failures and access control events"

# Processing and enrichment topics
create_topic "enriched-events" 6 3 "Events after AI analysis and threat intelligence enrichment"
create_topic "high-priority-events" 3 3 "High and critical severity events requiring immediate attention"

# Integration topics for MCP servers
create_topic "virustotal-requests" 2 3 "Requests to VirusTotal for IOC reputation checks"
create_topic "servicenow-requests" 2 3 "Requests to ServiceNow for incident management"
create_topic "cyberreason-requests" 2 3 "Requests to CyberReason for endpoint investigation"
create_topic "cloud-ivx-requests" 2 3 "Requests to Trellix Cloud IVX for malware analysis"

# Response and result topics
create_topic "analysis-results" 4 3 "Results from AI analysis and automated responses"
create_topic "incident-updates" 2 3 "Updates on incident status and resolution"

# Dead letter and error handling topics  
create_topic "failed-events" 2 3 "Events that failed processing for manual review"
create_topic "audit-trail" 3 3 "Audit trail of all processing actions and decisions"

# Metrics and monitoring topics
create_topic "platform-metrics" 2 3 "Platform performance and usage metrics"
create_topic "alert-notifications" 2 3 "Real-time alerts and notifications"

echo -e "${GREEN}✅ All topics created successfully!${NC}"
echo "================================="

# List all topics
echo -e "${BLUE}📋 Topic Summary:${NC}"
docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic list

echo ""
echo -e "${BLUE}💡 Usage Examples:${NC}"
echo "  • Publish to security-events:"
echo "    docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic produce security-events"
echo ""
echo "  • Consume from security-events:"
echo "    docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic consume security-events"
echo ""
echo "  • View topic details:"
echo "    docker exec $PROJECT_NAME-$BROKER_CONTAINER-1 rpk topic describe security-events"
echo ""
echo -e "${GREEN}🎉 Topics are ready for use!${NC}"