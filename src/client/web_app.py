"""
Web-based cybersecurity automation platform
FastAPI server with HTML frontend for event processing
"""

import json
import csv
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from .event_processor import EventProcessor
from .mcp_client import MCPClient
from .kafka_consumer import KafkaEventConsumer
from .bucket_client import BucketClient
from ..config.settings import AppConfig

class WebSecurityApp:
    """Web-based cybersecurity event processing application"""
    
    def __init__(self):
        self.app = FastAPI(title="AI Cybersecurity Agent - Web Interface")
        self.config = AppConfig()
        self.mcp_client = MCPClient(self.config.mcp_servers)
        self.event_processor = EventProcessor(self.mcp_client, self.config)
        self.kafka_consumer = KafkaEventConsumer()
        self.bucket_client = BucketClient(self.config.bucket_config)
        
        self.audit_logs = []
        self.processing_status = {"active": False, "progress": 0, "total": 0, "current_event": ""}
        self.websocket_connections = []
        
        # Setup directories
        self.setup_directories()
        
        # Setup routes
        self.setup_routes()
        
    def setup_directories(self):
        """Create necessary directories for web app"""
        base_dir = Path(__file__).parent.parent.parent
        self.templates_dir = base_dir / "templates"
        self.static_dir = base_dir / "static"
        self.uploads_dir = base_dir / "uploads"
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
        self.uploads_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 templates
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                "config": self.config.to_dict()
            })
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Handle file upload"""
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file selected")
            
            # Validate file type
            allowed_extensions = {'.json', '.csv', '.log', '.syslog'}
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JSON, CSV, LOG, SYSLOG")
            
            # Save uploaded file
            upload_path = self.uploads_dir / file.filename
            with open(upload_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Load and validate events
            try:
                events = self.load_events_from_file(str(upload_path))
                event_count = len(events)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
            
            self.log_audit(f"Uploaded file: {file.filename} ({event_count} events)")
            
            return {
                "filename": file.filename, 
                "event_count": event_count,
                "upload_path": str(upload_path)
            }
        
        @self.app.post("/api/process")
        async def process_events(
            request: Request,
            file_path: str = Form(...),
            prompt: str = Form(...)
        ):
            """Process uploaded events with AI analysis"""
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Prompt is required")
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail="File not found")
            
            # Start processing in background
            asyncio.create_task(self._process_events_async(file_path, prompt))
            
            return {"status": "processing_started", "message": "Event processing started"}
        
        @self.app.get("/api/status")
        async def get_processing_status():
            """Get current processing status"""
            return self.processing_status
        
        @self.app.get("/api/audit")
        async def get_audit_logs():
            """Get audit trail logs"""
            return {"logs": self.audit_logs[-100:]}  # Return last 100 logs
        
        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration"""
            return self.config.to_dict()
        
        @self.app.post("/api/kafka/start")
        async def start_kafka_consumer(topic: str = Form(...)):
            """Start Kafka consumer"""
            if not topic.strip():
                raise HTTPException(status_code=400, detail="Topic is required")
            
            try:
                # Start Kafka consumer in background
                asyncio.create_task(self._start_kafka_consumer(topic))
                self.log_audit(f"Started Kafka consumer for topic: {topic}")
                return {"status": "started", "topic": topic}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start Kafka consumer: {str(e)}")
        
        @self.app.post("/api/kafka/stop")
        async def stop_kafka_consumer():
            """Stop Kafka consumer"""
            try:
                self.kafka_consumer.stop_consuming()
                self.log_audit("Stopped Kafka consumer")
                return {"status": "stopped"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to stop Kafka consumer: {str(e)}")
        
        @self.app.get("/api/results/export")
        async def export_audit_logs():
            """Export audit logs as file"""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_log_{timestamp}.txt"
            filepath = self.uploads_dir / filename
            
            with open(filepath, 'w') as f:
                f.write("\n".join(self.audit_logs))
            
            return FileResponse(
                path=str(filepath),
                filename=filename,
                media_type='text/plain'
            )
        
        @self.app.get("/api/bucket/status")
        async def get_bucket_status():
            """Get S3 bucket status and list unprocessed files"""
            try:
                unprocessed_files = await self.bucket_client.list_unprocessed_files()
                return {
                    "bucket_name": self.config.bucket_config["bucket_name"],
                    "unprocessed_count": len(unprocessed_files),
                    "files": unprocessed_files
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to check bucket status: {str(e)}")
        
        @self.app.post("/api/bucket/process")
        async def process_bucket_files(prompt: str = Form(...)):
            """Process all unprocessed files in S3 bucket"""
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Prompt is required")
            
            # Start processing in background
            asyncio.create_task(self._process_bucket_files_async(prompt))
            
            return {"status": "processing_started", "message": "S3 bucket file processing started"}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and send periodic updates
                    await websocket.send_json({
                        "type": "status_update",
                        "data": self.processing_status
                    })
                    await asyncio.sleep(1)
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _process_events_async(self, file_path: str, prompt: str):
        """Process events asynchronously with status updates"""
        try:
            self.processing_status["active"] = True
            self.processing_status["progress"] = 0
            
            # Load events
            events = self.load_events_from_file(file_path)
            total_events = len(events)
            self.processing_status["total"] = total_events
            
            results = []
            
            # Process each event
            for i, event in enumerate(events):
                self.processing_status["progress"] = i + 1
                self.processing_status["current_event"] = f"Processing event {i+1}/{total_events}"
                
                self.log_audit(f"Processing event {i+1}/{total_events}")
                
                # Process single event
                result = await self.event_processor.process_event(event, prompt)
                results.append(result)
                
                # Broadcast update via WebSocket
                await self.broadcast_update({
                    "type": "processing_update",
                    "data": {
                        "progress": i + 1,
                        "total": total_events,
                        "result": result
                    }
                })
            
            self.processing_status["active"] = False
            self.processing_status["current_event"] = "Processing complete"
            self.log_audit(f"Completed processing {total_events} events")
            
            # Final broadcast
            await self.broadcast_update({
                "type": "processing_complete",
                "data": {"results": results}
            })
            
        except Exception as e:
            self.processing_status["active"] = False
            self.processing_status["current_event"] = f"Error: {str(e)}"
            self.log_audit(f"Error processing events: {str(e)}")
            
            await self.broadcast_update({
                "type": "error",
                "data": {"error": str(e)}
            })
    
    async def _start_kafka_consumer(self, topic: str):
        """Start Kafka consumer in background"""
        def handle_kafka_event(event_data):
            self.log_audit(f"Received Kafka event: {event_data}")
            # Process the event asynchronously
            asyncio.create_task(self._process_kafka_event(event_data))
        
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.kafka_consumer.start_consuming(topic, handle_kafka_event)
        )
    
    async def _process_kafka_event(self, event_data):
        """Process single Kafka event"""
        default_prompt = "Analyze this security event and take appropriate action"
        result = await self.event_processor.process_event(event_data, default_prompt)
        
        # Broadcast result via WebSocket
        await self.broadcast_update({
            "type": "kafka_event",
            "data": result
        })
    
    async def _process_bucket_files_async(self, prompt: str):
        """Process S3 bucket files asynchronously with status updates"""
        try:
            self.processing_status["active"] = True
            self.processing_status["progress"] = 0
            self.processing_status["current_event"] = "Checking S3 bucket for files"
            
            self.log_audit("Starting S3 bucket file processing")
            
            # Process files from bucket
            results = await self.bucket_client.process_bucket_files(self.event_processor, prompt)
            
            if not results:
                self.processing_status["active"] = False
                self.processing_status["current_event"] = "No unprocessed files found in bucket"
                self.log_audit("No unprocessed files found in bucket")
                
                await self.broadcast_update({
                    "type": "bucket_processing_complete",
                    "data": {"message": "No unprocessed files found", "results": []}
                })
                return
            
            # Update status
            self.processing_status["total"] = len(results)
            self.processing_status["progress"] = len(results)
            self.processing_status["active"] = False
            self.processing_status["current_event"] = f"Completed processing {len(results)} files from bucket"
            
            self.log_audit(f"Completed processing {len(results)} files from bucket")
            
            # Broadcast completion
            await self.broadcast_update({
                "type": "bucket_processing_complete",
                "data": {
                    "message": f"Successfully processed {len(results)} files",
                    "results": results
                }
            })
            
        except Exception as e:
            self.processing_status["active"] = False
            self.processing_status["current_event"] = f"Error: {str(e)}"
            error_msg = f"Failed to process bucket files: {str(e)}"
            self.log_audit(error_msg)
            
            await self.broadcast_update({
                "type": "bucket_error",
                "data": {"error": error_msg}
            })
    
    async def broadcast_update(self, message: dict):
        """Broadcast update to all WebSocket connections"""
        if self.websocket_connections:
            # Remove closed connections
            active_connections = []
            for connection in self.websocket_connections:
                try:
                    await connection.send_json(message)
                    active_connections.append(connection)
                except:
                    # Connection closed, skip it
                    pass
            self.websocket_connections = active_connections
    
    def load_events_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load events from JSON, CSV, or syslog file"""
        events = []
        
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    events = data
                else:
                    events = [data]
        elif file_path.endswith('.csv'):
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                events = list(reader)
        elif file_path.endswith('.log') or file_path.endswith('.syslog'):
            with open(file_path, 'r') as f:
                events = [line.strip() for line in f if line.strip()]
        else:
            # Auto-detect format
            with open(file_path, 'r') as f:
                content = f.read().strip()
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        events = data
                    else:
                        events = [data]
                except:
                    events = [line.strip() for line in content.split('\n') if line.strip()]
        
        return events
    
    def log_audit(self, message: str):
        """Add entry to audit log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audit_entry = f"[{timestamp}] {message}"
        self.audit_logs.append(audit_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the web application"""
        uvicorn.run(self.app, host=host, port=port)

# Create global app instance
web_app = WebSecurityApp()
app = web_app.app

if __name__ == "__main__":
    web_app.run()