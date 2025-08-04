#!/bin/bash

# Start Messaging Infrastructure (Redpanda Cluster)
# This script starts the Redpanda cluster with console for test/staging environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.redpanda.yml"
PROJECT_NAME="ai-soar-messaging"
CONSOLE_URL="http://localhost:8088"

echo -e "${BLUE}🚀 Starting AI-SOAR Messaging Infrastructure${NC}"
echo "============================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker first.${NC}"
    exit 1
fi

# Stop existing containers if running
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans 2>/dev/null || true

# Remove existing volumes if requested
if [[ "$1" == "--clean" ]]; then
    echo -e "${YELLOW}🧹 Cleaning up existing volumes...${NC}"
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v 2>/dev/null || true
    docker volume prune -f
fi

# Start the cluster
echo -e "${BLUE}🔄 Starting Redpanda cluster...${NC}"
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    echo -n "Checking $service_name"
    while [ $attempt -le $max_attempts ]; do
        if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps --format json | jq -r '.[] | select(.Service=="'$service_name'") | .Health' | grep -q "healthy"; then
            echo -e " ${GREEN}✅ Healthy${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo -e " ${RED}❌ Unhealthy${NC}"
    return 1
}

# Check each Redpanda node
for i in {1..3}; do
    if ! check_service_health "redpanda-$i"; then
        echo -e "${RED}❌ redpanda-$i failed to start properly${NC}"
        exit 1
    fi
done

# Check console
echo -n "Checking redpanda-console"
for i in {1..15}; do
    if curl -s $CONSOLE_URL > /dev/null 2>&1; then
        echo -e " ${GREEN}✅ Healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 15 ]; then
        echo -e " ${YELLOW}⚠️  Console may still be starting${NC}"
    fi
done

# Display cluster information
echo -e "\n${GREEN}✅ Messaging Infrastructure Started Successfully!${NC}"
echo "==============================================="
echo -e "${BLUE}📊 Cluster Information:${NC}"
echo "  • Redpanda Brokers:"
echo "    - redpanda-1: localhost:19092"
echo "    - redpanda-2: localhost:29092" 
echo "    - redpanda-3: localhost:39092"
echo "  • Schema Registry: localhost:18081"
echo "  • HTTP Proxy: localhost:18082"
echo "  • Admin API: localhost:19644"
echo ""
echo -e "${BLUE}🖥️  Redpanda Console:${NC}"
echo "  • URL: $CONSOLE_URL"
echo "  • Use the console to create topics, publish messages, and monitor the cluster"
echo ""
echo -e "${BLUE}🔗 Bootstrap Servers for Applications:${NC}"
echo "  • localhost:19092,localhost:29092,localhost:39092"
echo ""

# Check if topics script exists and offer to run it
if [[ -f "scripts/create_topics.sh" ]]; then
    echo -e "${YELLOW}💡 To create default topics, run: ./scripts/create_topics.sh${NC}"
fi

echo -e "${GREEN}🎉 Ready to process security events!${NC}"