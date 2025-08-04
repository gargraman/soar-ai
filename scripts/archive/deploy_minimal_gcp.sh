#!/bin/bash

# Minimal GCP Deployment - Just Infrastructure
# This creates a working system with basic services and messaging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="svc-hackathon-prod07"
VM_NAME="ai-soar-minimal"
ZONE="us-central1-a"
MACHINE_TYPE="n1-standard-4"
SERVICE_ACCOUNT="ai-soar-vm@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${BLUE}🚀 Minimal AI-SOAR Deployment to GCP${NC}"
echo "====================================="

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create minimal startup script that focuses on working infrastructure
cat > minimal-startup.sh << 'EOF'
#!/bin/bash

exec > >(tee /var/log/ai-soar-startup.log) 2>&1
echo "=== Minimal AI-SOAR Setup Started at $(date) ==="

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install basic packages
apt-get install -y python3 python3-pip git curl jq nginx

# Create application directory
mkdir -p /opt/ai-soar/logs
chown -R ubuntu:ubuntu /opt/ai-soar

# Create simple Redpanda setup
cat > /opt/ai-soar/docker-compose.yml << 'COMPOSE'
version: '3.8'
services:
  redpanda:
    image: redpandadata/redpanda:latest
    container_name: redpanda-single
    command:
      - redpanda start --kafka-addr internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr internal://redpanda:9092,external://localhost:19092
      - --pandaproxy-addr internal://0.0.0.0:8082,external://0.0.0.0:18082
      - --advertise-pandaproxy-addr internal://redpanda:8082,external://localhost:18082
      - --schema-registry-addr internal://0.0.0.0:8081,external://0.0.0.0:18081
      - --rpc-addr redpanda:33145
      - --advertise-rpc-addr redpanda:33145
      - --smp 1 --memory 1G --mode dev-container
    ports:
      - "19092:19092"  # Kafka
      - "18081:18081"  # Schema Registry
      - "18082:18082"  # HTTP Proxy
      - "9644:9644"    # Admin API
    networks:
      - ai-soar-net

  console:
    image: redpandadata/console:latest
    container_name: redpanda-console
    entrypoint: /bin/sh
    command: -c 'echo "$$CONSOLE_CONFIG_FILE" > /tmp/config.yml; /app/console'
    environment:
      CONFIG_FILEPATH: /tmp/config.yml
      CONSOLE_CONFIG_FILE: |
        kafka:
          brokers: ["redpanda:9092"]
        redpanda:
          adminApi:
            enabled: true
            urls: ["http://redpanda:9644"]
    ports:
      - "8088:8080"
    networks:
      - ai-soar-net
    depends_on:
      - redpanda

  # Simple web server
  web:
    image: nginx:alpine
    container_name: ai-soar-web
    ports:
      - "8080:80"
    volumes:
      - /opt/ai-soar/html:/usr/share/nginx/html:ro
    networks:
      - ai-soar-net

  # Mock API servers
  api-server:
    image: httpd:alpine
    container_name: ai-soar-api
    ports:
      - "8001:80"
      - "8002:80"
      - "8003:80"
      - "8004:80"
      - "8005:80"
    volumes:
      - /opt/ai-soar/api:/usr/local/apache2/htdocs:ro
    networks:
      - ai-soar-net

networks:
  ai-soar-net:
    driver: bridge
COMPOSE

# Create web content
mkdir -p /opt/ai-soar/html
cat > /opt/ai-soar/html/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>AI-SOAR Platform - Testing Environment</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .service { background: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #0066cc; }
        .service h3 { margin: 0 0 10px 0; color: #0066cc; }
        .service p { margin: 5px 0; color: #666; }
        .status { float: right; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .running { background: #d4edda; color: #155724; }
        .links { text-align: center; margin: 30px 0; }
        .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #0066cc; color: white; text-decoration: none; border-radius: 5px; }
        .links a:hover { background: #0052a3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI-SOAR Platform - Testing Environment</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            Cybersecurity Automation Platform with Event Streaming
        </p>

        <div class="service">
            <h3>Redpanda Console <span class="status running">RUNNING</span></h3>
            <p>Message streaming and topic management interface</p>
            <p><strong>Port:</strong> 8088 | <strong>Access:</strong> Via SSH tunnel</p>
        </div>

        <div class="service">
            <h3>MCP API Servers <span class="status running">RUNNING</span></h3>
            <p>Mock cybersecurity service endpoints for testing</p>
            <p><strong>Ports:</strong> 8001-8005 | <strong>Services:</strong> VirusTotal, ServiceNow, CyberReason, Custom REST, Cloud IVX</p>
        </div>

        <div class="service">
            <h3>Event Streaming <span class="status running">RUNNING</span></h3>
            <p>Kafka-compatible event processing with Redpanda</p>
            <p><strong>Bootstrap Servers:</strong> localhost:19092</p>
        </div>

        <div class="links">
            <a href="http://localhost:8088" target="_blank">📊 Redpanda Console</a>
            <a href="http://localhost:8001" target="_blank">🛡️ API Server 1</a>
            <a href="http://localhost:8002" target="_blank">🛡️ API Server 2</a>
        </div>

        <div style="margin-top: 40px; text-align: center; color: #999; font-size: 14px;">
            <p>🔒 Access via SSH tunnel: <code>./create_tunnels.sh</code></p>
            <p>📝 Deployment completed at $(date)</p>
        </div>
    </div>
</body>
</html>
HTML

# Create API mock responses
mkdir -p /opt/ai-soar/api
cat > /opt/ai-soar/api/index.html << 'API'
{
  "service": "AI-SOAR Mock API",
  "status": "healthy",
  "endpoints": [
    "/health",
    "/meta",
    "/api/v1/analyze"
  ],
  "message": "Mock API server for testing - Replace with actual MCP servers"
}
API

# Set permissions
chown -R ubuntu:ubuntu /opt/ai-soar

# Start services
cd /opt/ai-soar
sudo -u ubuntu docker-compose up -d

# Wait for services
sleep 30

# Create topics using redpanda
sudo -u ubuntu docker exec redpanda-single rpk topic create security-events --partitions 3 --replicas 1 2>/dev/null || true
sudo -u ubuntu docker exec redpanda-single rpk topic create malware-events --partitions 3 --replicas 1 2>/dev/null || true
sudo -u ubuntu docker exec redpanda-single rpk topic create network-events --partitions 3 --replicas 1 2>/dev/null || true

echo "=== Minimal AI-SOAR Setup Completed at $(date) ==="
echo "Services available:"
echo "  - Web Interface: http://localhost:8080"
echo "  - Redpanda Console: http://localhost:8088"
echo "  - Mock APIs: http://localhost:8001-8005"
echo "  - Kafka: localhost:19092"
EOF

# Delete existing VM if needed
if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    print_warning "Deleting existing VM: $VM_NAME"
    gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
fi

# Get subnet info
SUBNET_INFO=$(gcloud compute networks subnets list --format="value(name,region,network)" | head -1)
SUBNET_NAME=$(echo $SUBNET_INFO | cut -d' ' -f1)

print_status "Creating minimal VM with startup script..."
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-ssd \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --subnet=$SUBNET_NAME \
    --tags=ai-soar-server \
    --service-account=$SERVICE_ACCOUNT \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --metadata-from-file startup-script=minimal-startup.sh

VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Create tunnel script
cat > create_minimal_tunnels.sh << EOF
#!/bin/bash
echo "🔗 Creating SSH tunnels to minimal AI-SOAR services..."
gcloud compute ssh $VM_NAME --zone=$ZONE -- \\
    -L 8080:localhost:8080 \\
    -L 8088:localhost:8088 \\
    -L 8001:localhost:8001 \\
    -L 19092:localhost:19092 \\
    -N
EOF
chmod +x create_minimal_tunnels.sh

echo ""
echo -e "${GREEN}✅ Minimal AI-SOAR VM created!${NC}"
echo "=============================="
echo ""
echo -e "${BLUE}📋 VM Details:${NC}"
echo "  • Name: $VM_NAME"
echo "  • Zone: $ZONE"
echo "  • External IP: $VM_IP"
echo ""
echo -e "${BLUE}⏳ Services starting automatically (3-5 minutes)...${NC}"
echo "  Monitor: gcloud compute instances get-serial-port-output $VM_NAME --zone=$ZONE"
echo ""
echo -e "${BLUE}🔗 Access Services:${NC}"
echo "  1. Run: ./create_minimal_tunnels.sh"
echo "  2. Open: http://localhost:8080"
echo "  3. Redpanda Console: http://localhost:8088"
echo ""
echo -e "${YELLOW}💡 This is a minimal setup focused on working infrastructure!${NC}"

# Clean up
rm minimal-startup.sh

print_status "🎉 Minimal deployment initiated!"