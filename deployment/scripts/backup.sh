#!/bin/bash

# Backup Script for AI SOAR Platform
# Usage: ./backup.sh

set -e

# Configuration
PROJECT_ID="svc-hackathon-prod07"
BACKUP_BUCKET="ai-soar-backups-prod07"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/ai-soar"
LOG_DIR="/var/log/ai-soar"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}💾 Starting AI SOAR Platform Backup${NC}"
echo "======================================"

# Create local backup directory
BACKUP_DIR="/tmp/ai-soar-backup-$BACKUP_DATE"
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}📁 Creating local backup directory: $BACKUP_DIR${NC}"

# Backup application configuration
echo -e "${GREEN}⚙️ Backing up configuration files...${NC}"
cp -r "$APP_DIR/deployment/config" "$BACKUP_DIR/"
cp "$APP_DIR/.env" "$BACKUP_DIR/" 2>/dev/null || echo "No .env file found"

# Backup logs (last 7 days)
echo -e "${GREEN}📄 Backing up recent logs...${NC}"
mkdir -p "$BACKUP_DIR/logs"
find "$LOG_DIR" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null || echo "No recent logs found"

# Backup database (if exists)
echo -e "${GREEN}🗄️ Backing up application data...${NC}"
if [ -d "$APP_DIR/data" ]; then
    cp -r "$APP_DIR/data" "$BACKUP_DIR/"
fi

# Export Docker container configurations
echo -e "${GREEN}🐳 Backing up Docker configurations...${NC}"
docker-compose -f "$APP_DIR/deployment/docker-compose.yml" config > "$BACKUP_DIR/docker-compose-resolved.yml"

# Create system information snapshot
echo -e "${GREEN}📊 Creating system snapshot...${NC}"
cat > "$BACKUP_DIR/system-info.txt" << EOF
Backup Date: $(date)
Hostname: $(hostname)
OS Version: $(lsb_release -d | cut -f2)
Docker Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)
Python Version: $(python3 --version)
Disk Usage: $(df -h /)
Memory Usage: $(free -h)
Running Containers: $(docker ps --format "table {{.Names}}\t{{.Status}}")
EOF

# Create tar archive
ARCHIVE_NAME="ai-soar-backup-$BACKUP_DATE.tar.gz"
echo -e "${GREEN}📦 Creating archive: $ARCHIVE_NAME${NC}"
tar -czf "/tmp/$ARCHIVE_NAME" -C "/tmp" "ai-soar-backup-$BACKUP_DATE"

# Upload to Google Cloud Storage
echo -e "${GREEN}☁️ Uploading to Google Cloud Storage...${NC}"
if gsutil cp "/tmp/$ARCHIVE_NAME" "gs://$BACKUP_BUCKET/"; then
    echo -e "${GREEN}✓ Backup uploaded successfully${NC}"
    
    # Clean up local files
    rm -rf "$BACKUP_DIR"
    rm "/tmp/$ARCHIVE_NAME"
    
    echo -e "${GREEN}🧹 Local backup files cleaned up${NC}"
else
    echo "❌ Failed to upload backup to Cloud Storage"
    echo "Local backup available at: /tmp/$ARCHIVE_NAME"
    exit 1
fi

# Clean up old backups (keep last 30 days)
echo -e "${GREEN}🗑️ Cleaning up old backups...${NC}"
gsutil -m rm -r "gs://$BACKUP_BUCKET/ai-soar-backup-$(date -d '30 days ago' +%Y%m%d)*" 2>/dev/null || echo "No old backups to clean"

echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo "Backup location: gs://$BACKUP_BUCKET/$ARCHIVE_NAME"