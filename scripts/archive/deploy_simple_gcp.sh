#!/bin/bash

# Simple GCP Deployment - Manual Steps Approach
# This script creates the VM and provides manual instructions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="svc-hackathon-prod07"
VM_NAME="ai-soar-vm"
ZONE="us-central1-a"
MACHINE_TYPE="n1-standard-4"

echo -e "${BLUE}🚀 Simple AI-SOAR Platform Deployment to GCP${NC}"
echo "=============================================="

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    print_status "VM already exists with IP: $VM_IP"
else
    print_error "VM $VM_NAME not found in zone $ZONE"
    echo "Please create the VM first or run the main deployment script."
    exit 1
fi

# Create a comprehensive manual setup script
print_status "Creating manual setup instructions..."

cat > manual_vm_setup.sh << 'EOF'
#!/bin/bash

# Manual VM Setup Script for AI-SOAR Platform
# Run this script on the VM after SSH connection

set -e

echo "🔧 Setting up AI-SOAR Platform on VM..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv git curl

# Create application directory
sudo mkdir -p /opt/ai-soar
sudo chown $USER:$USER /opt/ai-soar
cd /opt/ai-soar

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
source ~/.bashrc

echo "✅ Basic setup completed!"
echo "Next steps:"
echo "1. Copy application files to /opt/ai-soar/"
echo "2. Set up virtual environment: python3 -m venv venv"
echo "3. Install dependencies: source venv/bin/activate && pip install -r requirements.txt"
echo "4. Configure environment variables"
echo "5. Start services with docker-compose"
EOF

chmod +x manual_vm_setup.sh

# Create SSH connection helper
cat > connect_to_vm.sh << EOF
#!/bin/bash

# Helper script to connect to the AI-SOAR VM
VM_NAME="$VM_NAME"
ZONE="$ZONE"
VM_IP="$VM_IP"

echo "🔗 Connecting to AI-SOAR VM..."
echo "VM Name: \$VM_NAME"
echo "Zone: \$ZONE"
echo "External IP: \$VM_IP"
echo ""

# Try different connection methods
echo "Trying standard SSH connection..."
if gcloud compute ssh \$VM_NAME --zone=\$ZONE --command="echo 'Connection successful'"; then
    echo "✅ Standard SSH works!"
    gcloud compute ssh \$VM_NAME --zone=\$ZONE
elif gcloud compute ssh \$VM_NAME --zone=\$ZONE --tunnel-through-iap --command="echo 'IAP connection successful'"; then
    echo "✅ IAP tunnel works!"
    gcloud compute ssh \$VM_NAME --zone=\$ZONE --tunnel-through-iap
else
    echo "❌ SSH connection failed. Trying alternative methods..."
    echo ""
    echo "Try these alternatives:"
    echo "1. Wait 5 minutes for VM to fully boot, then retry"
    echo "2. Check firewall rules:"
    echo "   gcloud compute firewall-rules list"
    echo "3. Create SSH firewall rule if needed:"
    echo "   gcloud compute firewall-rules create allow-ssh --allow tcp:22 --source-ranges 0.0.0.0/0"
    echo "4. Use GCP Console web SSH"
fi
EOF

chmod +x connect_to_vm.sh

# Create file transfer helper
cat > transfer_files.sh << EOF
#!/bin/bash

# Helper script to transfer files to the VM
VM_NAME="$VM_NAME"
ZONE="$ZONE"

echo "📁 Transferring application files to VM..."

# Create temporary archive of required files
tar -czf ai-soar-app.tar.gz \\
    src/ \\
    deployment/ \\
    scripts/ \\
    requirements.txt \\
    main.py \\
    web_main.py \\
    launch_servers.py \\
    launch_web_app.py \\
    docker-compose.redpanda.yml

echo "Created application archive: ai-soar-app.tar.gz"

# Try to transfer files
if gcloud compute scp ai-soar-app.tar.gz \$VM_NAME:/tmp/ --zone=\$ZONE; then
    echo "✅ Files transferred successfully!"
    echo ""
    echo "Next steps:"
    echo "1. SSH to VM: ./connect_to_vm.sh"
    echo "2. Extract files: cd /opt/ai-soar && tar -xzf /tmp/ai-soar-app.tar.gz"
    echo "3. Run setup: ./manual_vm_setup.sh"
elif gcloud compute scp ai-soar-app.tar.gz \$VM_NAME:/tmp/ --zone=\$ZONE --tunnel-through-iap; then
    echo "✅ Files transferred via IAP tunnel!"
    echo "Follow the next steps above."
else
    echo "❌ File transfer failed."
    echo "Alternative: Use GCP Console to upload files or clone from Git repository"
fi

# Clean up
rm ai-soar-app.tar.gz
EOF

chmod +x transfer_files.sh

# Create comprehensive deployment instructions
cat > DEPLOYMENT_INSTRUCTIONS.md << EOF
# AI-SOAR Manual Deployment Instructions

## Current Status
- ✅ VM Created: $VM_NAME (IP: $VM_IP)
- ⏳ Manual setup required

## Step-by-Step Deployment

### 1. Connect to VM
\`\`\`bash
./connect_to_vm.sh
\`\`\`

### 2. Transfer Application Files
\`\`\`bash
./transfer_files.sh
\`\`\`

### 3. SSH to VM and Setup
\`\`\`bash
# On the VM
cd /opt/ai-soar
tar -xzf /tmp/ai-soar-app.tar.gz
./manual_vm_setup.sh
\`\`\`

### 4. Install Application Dependencies
\`\`\`bash
# On the VM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 5. Configure Environment
\`\`\`bash
# On the VM
cp deployment/config/staging.env .env
# Edit .env file as needed
\`\`\`

### 6. Start Services
\`\`\`bash
# On the VM
# Start messaging infrastructure
./scripts/start_messaging_infra.sh

# Start application services
docker-compose -f deployment/docker-compose.yml up -d

# Create Kafka topics
./scripts/create_topics.sh
\`\`\`

### 7. Access Services via SSH Tunnels
Create SSH tunnels from your local machine:
\`\`\`bash
gcloud compute ssh $VM_NAME --zone=$ZONE -- \\
    -L 8080:localhost:8080 \\
    -L 8088:localhost:8088 \\
    -L 8001:localhost:8001 \\
    -L 8002:localhost:8002 \\
    -L 8003:localhost:8003 \\
    -L 8004:localhost:8004 \\
    -L 8005:localhost:8005 \\
    -N
\`\`\`

Then access:
- Web Application: http://localhost:8080
- Redpanda Console: http://localhost:8088
- API Servers: http://localhost:8001-8005

## Troubleshooting

### SSH Connection Issues
1. Wait 5-10 minutes for VM to fully boot
2. Try IAP tunnel: \`gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap\`
3. Use GCP Console web SSH as fallback

### File Transfer Issues
1. Use IAP tunnel for scp
2. Clone directly from Git repository on VM
3. Use GCP Console file upload

### Service Issues
1. Check logs: \`docker-compose logs -f\`
2. Verify ports: \`netstat -tlnp\`
3. Check firewall: \`sudo ufw status\`
EOF

echo ""
echo -e "${GREEN}✅ Manual deployment setup completed!${NC}"
echo "========================================="
echo ""
echo -e "${BLUE}📋 What was created:${NC}"
echo "  • VM: $VM_NAME (IP: $VM_IP)"
echo "  • Helper scripts:"
echo "    - connect_to_vm.sh - Connect to VM"
echo "    - transfer_files.sh - Transfer application files"
echo "    - manual_vm_setup.sh - Run on VM for setup"
echo "  • DEPLOYMENT_INSTRUCTIONS.md - Complete guide"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Run: ./transfer_files.sh"
echo "2. Run: ./connect_to_vm.sh"
echo "3. Follow instructions in DEPLOYMENT_INSTRUCTIONS.md"
echo ""
echo -e "${YELLOW}💡 This approach gives you full control over each step!${NC}"