#!/bin/bash

# Deploy AI-SOAR Platform to Google Cloud Platform (Restricted Permissions Version)
# This script works with limited firewall permissions using SSH tunneling

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
SERVICE_ACCOUNT="ai-soar-vm@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${BLUE}🚀 Deploying AI-SOAR Platform to Google Cloud (Restricted Mode)${NC}"
echo "================================================================="

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    print_error "Not authenticated with Google Cloud. Please run: gcloud auth login"
    exit 1
fi

# Set project
print_status "Setting Google Cloud project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com || print_warning "Some APIs may already be enabled"

# Create service account if it doesn't exist
print_status "Creating service account..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &>/dev/null; then
    gcloud iam service-accounts create ai-soar-vm \
        --display-name="AI SOAR VM Service Account"
    
    # Grant required permissions
    for role in "roles/aiplatform.user" "roles/secretmanager.secretAccessor" "roles/logging.logWriter" "roles/monitoring.metricWriter"; do
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="$role" || print_warning "Role $role may already be assigned"
    done
    print_status "Service account created and configured"
else
    print_status "Service account already exists"
fi

# Check available subnets
print_status "Checking available subnets..."
SUBNET_INFO=$(gcloud compute networks subnets list --format="value(name,region,network)" | head -1)
if [ -z "$SUBNET_INFO" ]; then
    print_error "No subnets available. Please ask admin to create a subnet."
    exit 1
fi

SUBNET_NAME=$(echo $SUBNET_INFO | cut -d' ' -f1)
SUBNET_REGION=$(echo $SUBNET_INFO | cut -d' ' -f2)
NETWORK_NAME=$(echo $SUBNET_INFO | cut -d' ' -f3)

print_status "Using subnet: $SUBNET_NAME in region: $SUBNET_REGION (network: $NETWORK_NAME)"

# Update zone to match subnet region if needed
if [[ "$ZONE" != "$SUBNET_REGION"* ]]; then
    ZONE="$SUBNET_REGION-a"
    print_status "Updated zone to: $ZONE to match subnet region"
fi

# Skip firewall rules creation - use SSH tunneling instead
print_warning "Skipping firewall rules creation - using SSH tunneling for access"

# Create VM instance
print_status "Creating VM instance..."
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --boot-disk-size=100GB \
        --boot-disk-type=pd-ssd \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --subnet=$SUBNET_NAME \
        --tags=ai-soar-server \
        --service-account=$SERVICE_ACCOUNT \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --metadata-from-file startup-script=deployment/vm-setup.sh
    
    print_status "VM instance created successfully"
    
    # Wait for VM to be ready
    print_status "Waiting for VM to be ready..."
    sleep 30
    
    # Wait for startup script to complete
    print_status "Waiting for startup script to complete (this may take 5-10 minutes)..."
    timeout=300  # 5 minutes timeout
    elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if gcloud compute instances get-serial-port-output $VM_NAME --zone=$ZONE 2>/dev/null | grep -q "VM setup completed successfully"; then
            break
        fi
        echo -n "."
        sleep 10
        elapsed=$((elapsed + 10))
    done
    echo ""
    
    if [ $elapsed -ge $timeout ]; then
        print_warning "Startup script may still be running. Continuing with deployment..."
    else
        print_status "VM setup completed"
    fi
else
    print_status "VM instance already exists"
fi

# Get VM external IP
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
print_status "VM External IP: $VM_IP"

# Copy application files to VM
print_status "Copying application files to VM..."
gcloud compute scp --recurse \
    ./src ./deployment ./requirements.txt ./scripts ./docker-compose.redpanda.yml \
    ./main.py ./web_main.py ./launch_servers.py ./launch_web_app.py \
    $VM_NAME:/opt/ai-soar/ \
    --zone=$ZONE

# Deploy configuration
print_status "Deploying configuration..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    cd /opt/ai-soar
    
    # Copy staging configuration
    cp deployment/config/staging.env .env
    
    # Update configuration for internal access
    sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0/' .env
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Build and start services
    docker-compose -f deployment/docker-compose.yml build
    docker-compose -f deployment/docker-compose.yml up -d
    
    # Start messaging infrastructure
    chmod +x scripts/*.sh
    ./scripts/start_messaging_infra.sh
    
    # Wait for services to be ready
    sleep 30
    
    # Create Kafka topics
    ./scripts/create_topics.sh
    
    echo 'Deployment completed successfully!'
"

# Create SSH tunnel script
print_status "Creating SSH tunnel script..."
cat > ssh_tunnel.sh << EOF
#!/bin/bash

# SSH Tunnel Script for AI-SOAR Platform
# This script creates SSH tunnels to access services running on GCP VM

VM_NAME="$VM_NAME"
ZONE="$ZONE"

echo "🔗 Creating SSH tunnels to AI-SOAR services..."

# Kill existing tunnels
pkill -f "ssh.*$VM_NAME.*-L" 2>/dev/null || true

# Create tunnels for all services
gcloud compute ssh \$VM_NAME --zone=\$ZONE -- \\
    -L 8080:localhost:8080 \\
    -L 8001:localhost:8001 \\
    -L 8002:localhost:8002 \\
    -L 8003:localhost:8003 \\
    -L 8004:localhost:8004 \\
    -L 8005:localhost:8005 \\
    -L 8088:localhost:8088 \\
    -L 19092:localhost:19092 \\
    -L 29092:localhost:29092 \\
    -L 39092:localhost:39092 \\
    -N

echo "SSH tunnels closed."
EOF

chmod +x ssh_tunnel.sh

# Display completion information
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "========================================="
echo ""
echo -e "${BLUE}🌐 Access Methods:${NC}"
echo "  • VM External IP: $VM_IP (internal access only)"
echo ""
echo -e "${YELLOW}🔗 SSH Tunnel Access (Recommended):${NC}"
echo "  1. Run SSH tunnel: ./ssh_tunnel.sh"
echo "  2. Access services locally:"
echo "     • Web Application: http://localhost:8080"
echo "     • VirusTotal Server: http://localhost:8001"
echo "     • ServiceNow Server: http://localhost:8002"
echo "     • CyberReason Server: http://localhost:8003"
echo "     • Custom REST Server: http://localhost:8004"
echo "     • Cloud IVX Server: http://localhost:8005"
echo "     • Redpanda Console: http://localhost:8088"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "  • SSH to VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "  • View logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='docker-compose logs -f'"
echo "  • Stop VM: gcloud compute instances stop $VM_NAME --zone=$ZONE"
echo "  • Start VM: gcloud compute instances start $VM_NAME --zone=$ZONE"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "1. Run: ./ssh_tunnel.sh (in a separate terminal)"
echo "2. Open http://localhost:8080 in your browser"
echo "3. Use Redpanda Console at http://localhost:8088"
echo "4. Update API keys in Secret Manager if needed"
echo ""

print_status "🎉 AI-SOAR Platform is now running on Google Cloud with SSH tunnel access!"