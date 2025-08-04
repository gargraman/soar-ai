# AI-SOAR Messaging Infrastructure

This directory contains scripts to set up and manage the Redpanda-based messaging infrastructure for the AI-SOAR platform in test/staging environments.

## Overview

The messaging infrastructure uses Redpanda as a Kafka-compatible event streaming platform with the following components:

- **3-node Redpanda cluster** for high availability
- **Redpanda Console** for message management and monitoring
- **Pre-configured topics** for different event types
- **Sample event publishers** for testing

## Quick Start

### 1. Start the Messaging Infrastructure

```bash
# Start the complete Redpanda cluster with console
./scripts/start_messaging_infra.sh

# Start with clean volumes (removes all existing data)
./scripts/start_messaging_infra.sh --clean
```

### 2. Create Topics

```bash
# Create all required topics for the platform
./scripts/create_topics.sh
```

### 3. Publish Sample Events

```bash
# Publish sample security events to various topics
./scripts/publish_sample_events.sh
```

### 4. Access the Console

Open your browser to: http://localhost:8088

The Redpanda Console provides a web interface to:
- View and manage topics
- Publish and consume messages
- Monitor cluster health
- View consumer groups

## Architecture

### Cluster Configuration

| Component | External Port | Internal Port | Description |
|-----------|---------------|---------------|-------------|
| Redpanda-1 | 19092 | 9092 | Kafka API (Primary broker) |
| Redpanda-2 | 29092 | 9092 | Kafka API (Secondary broker) |
| Redpanda-3 | 39092 | 9092 | Kafka API (Tertiary broker) |
| Console | 8088 | 8080 | Web UI for management |
| Schema Registry | 18081 | 8081 | Schema management |
| HTTP Proxy | 18082 | 8082 | REST API access |

### Bootstrap Servers

For application connections:
```
localhost:19092,localhost:29092,localhost:39092
```

## Topics

The platform uses the following topic structure:

### Security Event Topics
- `security-events` - Main topic for all security events
- `malware-events` - Malware detection events
- `network-events` - Network anomalies and intrusions
- `endpoint-events` - Host-based security events
- `authentication-events` - Authentication and access control events

### Processing Topics
- `enriched-events` - Events after AI analysis
- `high-priority-events` - Critical severity events
- `analysis-results` - AI analysis results
- `incident-updates` - Incident status updates

### Integration Topics
- `virustotal-requests` - VirusTotal API requests
- `servicenow-requests` - ServiceNow integration
- `cyberreason-requests` - CyberReason endpoint queries
- `cloud-ivx-requests` - Trellix Cloud IVX requests

### System Topics
- `failed-events` - Failed processing events
- `audit-trail` - Processing audit logs
- `platform-metrics` - Performance metrics
- `alert-notifications` - Real-time alerts

## Scripts Reference

### `start_messaging_infra.sh`
Starts the complete Redpanda cluster with console.

**Options:**
- `--clean` - Remove existing volumes and start fresh

**Services Started:**
- 3 Redpanda brokers (redpanda-1, redpanda-2, redpanda-3)
- Redpanda Console for web management
- Health checks for all services

### `create_topics.sh`
Creates all required topics with appropriate partitions and replication.

**Topic Configuration:**
- Partitions: 2-6 (based on expected load)
- Replication Factor: 3 (for high availability)
- Retention: 7 days
- Cleanup Policy: Delete

### `publish_sample_events.sh`
Publishes sample security events to demonstrate the platform.

**Sample Events:**
- Malware detection
- Network anomalies
- Authentication failures
- Privilege escalation
- Data exfiltration
- Critical APT activity

### `stop_messaging_infra.sh`
Stops the messaging infrastructure.

**Options:**
- `--clean` - Remove volumes and all data
- `--force` - Skip confirmation prompts

## Usage Examples

### Command Line Operations

```bash
# List all topics
docker exec ai-soar-messaging-redpanda-1-1 rpk topic list

# Describe a topic
docker exec ai-soar-messaging-redpanda-1-1 rpk topic describe security-events

# Produce messages
echo '{"event": "test"}' | docker exec -i ai-soar-messaging-redpanda-1-1 rpk topic produce security-events

# Consume messages  
docker exec ai-soar-messaging-redpanda-1-1 rpk topic consume security-events --print-headers

# Check cluster status
docker exec ai-soar-messaging-redpanda-1-1 rpk cluster health
```

### Application Integration

```python
from kafka import KafkaProducer, KafkaConsumer
import json

# Producer example
producer = KafkaProducer(
    bootstrap_servers=['localhost:19092', 'localhost:29092', 'localhost:39092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

event = {
    "id": "evt_001",
    "event_type": "malware_detection",
    "severity": "high",
    "hostname": "workstation-01"
}

producer.send('security-events', event)

# Consumer example
consumer = KafkaConsumer(
    'security-events',
    bootstrap_servers=['localhost:19092', 'localhost:29092', 'localhost:39092'],
    group_id='ai-soar-consumer-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    print(f"Received: {message.value}")
```

## Monitoring and Management

### Health Checks

```bash
# Check cluster health
docker exec ai-soar-messaging-redpanda-1-1 rpk cluster health

# Check node status
docker compose -p ai-soar-messaging ps

# View logs
docker compose -p ai-soar-messaging logs -f redpanda-1
```

### Performance Monitoring

Access metrics through:
- Redpanda Console: http://localhost:8088
- Admin API: http://localhost:19644/metrics
- Prometheus metrics endpoint available

## Troubleshooting

### Common Issues

1. **Cluster not starting**
   ```bash
   # Check Docker daemon
   docker info
   
   # Check port conflicts
   netstat -tuln | grep -E '(19092|29092|39092|8088)'
   
   # Clean start
   ./scripts/stop_messaging_infra.sh --clean
   ./scripts/start_messaging_infra.sh
   ```

2. **Topics not accessible**
   ```bash
   # Verify cluster health
   docker exec ai-soar-messaging-redpanda-1-1 rpk cluster health
   
   # Check topic exists
   docker exec ai-soar-messaging-redpanda-1-1 rpk topic list
   ```

3. **Console not accessible**
   ```bash
   # Check console logs
   docker compose -p ai-soar-messaging logs redpanda-console
   
   # Verify console is running
   curl http://localhost:8088
   ```

### Log Locations

- Container logs: `docker compose -p ai-soar-messaging logs [service]`
- Redpanda data: Docker volumes `ai-soar-messaging_redpanda-[1-3]`

## Configuration Files

- `docker-compose.redpanda.yml` - Docker Compose configuration
- `src/config/settings.py` - Application Kafka configuration

## Production Considerations

For production deployment:
- Use external load balancer for broker access
- Configure authentication and SSL/TLS
- Set up monitoring with Prometheus/Grafana
- Configure proper retention policies
- Use dedicated storage volumes
- Set resource limits and requests

## VM Deployment

For VM deployment, ensure:
- Docker and Docker Compose installed
- Sufficient resources (minimum 4GB RAM, 2 CPU cores)
- Ports 8088, 19092, 29092, 39092 accessible
- Firewall rules configured appropriately