#!/bin/bash

# Stop Messaging Infrastructure (Redpanda Cluster)
# This script stops and optionally cleans up the Redpanda cluster

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

echo -e "${BLUE}🛑 Stopping AI-SOAR Messaging Infrastructure${NC}"
echo "=============================================="

# Parse command line arguments
CLEAN_VOLUMES=false
FORCE_REMOVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_VOLUMES=true
            shift
            ;;
        --force)
            FORCE_REMOVE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean    Remove volumes and all data"
            echo "  --force    Force removal without confirmation"
            echo "  -h, --help Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Confirmation for clean operation
if [[ "$CLEAN_VOLUMES" == true && "$FORCE_REMOVE" != true ]]; then
    echo -e "${YELLOW}⚠️  This will remove all data and volumes. Are you sure? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Operation cancelled.${NC}"
        exit 0
    fi
fi

# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi

# Stop containers
echo -e "${YELLOW}🔄 Stopping containers...${NC}"
if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps -q &>/dev/null; then
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME stop
    echo -e "${GREEN}✅ Containers stopped${NC}"
else
    echo -e "${YELLOW}ℹ️  No running containers found${NC}"
fi

# Remove containers
echo -e "${YELLOW}🗑️  Removing containers...${NC}"
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans
echo -e "${GREEN}✅ Containers removed${NC}"

# Clean volumes if requested
if [[ "$CLEAN_VOLUMES" == true ]]; then
    echo -e "${YELLOW}🧹 Cleaning up volumes...${NC}"
    
    # Remove project volumes
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v
    
    # Remove dangling volumes
    echo -e "${YELLOW}🔄 Removing dangling volumes...${NC}"
    docker volume prune -f
    
    echo -e "${GREEN}✅ Volumes cleaned up${NC}"
fi

# Clean up networks
echo -e "${YELLOW}🌐 Cleaning up networks...${NC}"
docker network prune -f
echo -e "${GREEN}✅ Networks cleaned up${NC}"

# Show final status
echo ""
echo -e "${GREEN}✅ Messaging Infrastructure Stopped Successfully!${NC}"
echo "================================================="

if [[ "$CLEAN_VOLUMES" == true ]]; then
    echo -e "${BLUE}ℹ️  All data has been removed. You'll lost all topics and messages.${NC}"
    echo -e "${BLUE}ℹ️  Run ./scripts/start_messaging_infra.sh to start fresh.${NC}"
else
    echo -e "${BLUE}ℹ️  Data volumes preserved. Topics and messages are still available.${NC}"
    echo -e "${BLUE}ℹ️  Run ./scripts/start_messaging_infra.sh to restart the cluster.${NC}"
fi

echo -e "${GREEN}🎉 Cleanup completed!${NC}"