# AI-SOAR Manual Deployment Instructions

## Current Status
- ✅ VM Created: ai-soar-vm (IP: 35.236.25.85)
- ⏳ Manual setup required

## Step-by-Step Deployment

### 1. Connect to VM
```bash
./connect_to_vm.sh
```

### 2. Transfer Application Files
```bash
./transfer_files.sh
```

### 3. SSH to VM and Setup
```bash
# On the VM
cd /opt/ai-soar
tar -xzf /tmp/ai-soar-app.tar.gz
./manual_vm_setup.sh
```

### 4. Install Application Dependencies
```bash
# On the VM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment
```bash
# On the VM
cp deployment/config/staging.env .env
# Edit .env file as needed
```

### 6. Start Services
```bash
# On the VM
# Start messaging infrastructure
./scripts/start_messaging_infra.sh

# Start application services
docker-compose -f deployment/docker-compose.yml up -d

# Create Kafka topics
./scripts/create_topics.sh
```

### 7. Access Services via SSH Tunnels
Create SSH tunnels from your local machine:
```bash
gcloud compute ssh ai-soar-vm --zone=us-west2-a -- \
    -L 8080:localhost:8080 \
    -L 8088:localhost:8088 \
    -L 8001:localhost:8001 \
    -L 8002:localhost:8002 \
    -L 8003:localhost:8003 \
    -L 8004:localhost:8004 \
    -L 8005:localhost:8005 \
    -N
```

Then access:
- Web Application: http://localhost:8080
- Redpanda Console: http://localhost:8088
- API Servers: http://localhost:8001-8005

## Troubleshooting

### SSH Connection Issues
1. Wait 5-10 minutes for VM to fully boot
2. Try IAP tunnel: `gcloud compute ssh ai-soar-vm --zone=us-west2-a --tunnel-through-iap`
3. Use GCP Console web SSH as fallback

### File Transfer Issues
1. Use IAP tunnel for scp
2. Clone directly from Git repository on VM
3. Use GCP Console file upload

### Service Issues
1. Check logs: `docker-compose logs -f`
2. Verify ports: `netstat -tlnp`
3. Check firewall: `sudo ufw status`
