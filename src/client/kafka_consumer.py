
import json
import threading
import time
from typing import Callable, Optional, Dict, Any

# Mock Kafka consumer for demo purposes
# In production, you would use kafka-python or confluent-kafka
class KafkaEventConsumer:
    """Kafka consumer for streaming security events"""
    
    def __init__(self):
        self.consuming = False
        self.consumer_thread = None
        
    def start_consuming(self, topic: str, event_handler: Callable[[Dict[str, Any]], None]):
        """Start consuming events from Kafka topic"""
        self.consuming = True
        self.consumer_thread = threading.Thread(
            target=self._consume_loop, 
            args=(topic, event_handler),
            daemon=True
        )
        self.consumer_thread.start()
        
    def stop_consuming(self):
        """Stop consuming events"""
        self.consuming = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
            
    def _consume_loop(self, topic: str, event_handler: Callable[[Dict[str, Any]], None]):
        """Main consumption loop (mock implementation)"""
        
        # Mock events for demonstration
        mock_events = [
            {
                "id": "evt_001",
                "timestamp": "2024-01-20T10:30:00Z",
                "event_type": "malware_detection",
                "severity": "high",
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.5",
                "hostname": "workstation-01",
                "description": "Suspicious file detected",
                "indicators": {
                    "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
                    "file_path": "/tmp/suspicious.exe"
                }
            },
            {
                "id": "evt_002", 
                "timestamp": "2024-01-20T10:35:00Z",
                "event_type": "network_anomaly",
                "severity": "medium",
                "source_ip": "192.168.1.50",
                "destination_domain": "malicious-domain.com",
                "hostname": "server-02",
                "description": "Unusual network traffic detected"
            },
            {
                "id": "evt_003",
                "timestamp": "2024-01-20T10:40:00Z", 
                "event_type": "failed_login",
                "severity": "low",
                "source_ip": "203.0.113.45",
                "hostname": "web-server-01",
                "username": "admin",
                "description": "Multiple failed login attempts"
            }
        ]
        
        event_index = 0
        
        while self.consuming:
            try:
                # Simulate receiving an event every 10 seconds
                time.sleep(10)
                
                if event_index < len(mock_events):
                    event = mock_events[event_index].copy()
                    event["kafka_topic"] = topic
                    event["received_at"] = time.time()
                    
                    event_handler(event)
                    event_index = (event_index + 1) % len(mock_events)
                    
            except Exception as e:
                print(f"Error in Kafka consumer: {e}")
                break
