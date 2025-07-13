
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import datetime
import uvicorn

app = FastAPI(title="ServiceNow MCP Server", version="1.0.0")

class CreateRecordRequest(BaseModel):
    type: str  # incident, task, etc.
    summary: str
    description: str
    severity: Optional[str] = "medium"
    assigned_to: Optional[str] = None

class GetRecordRequest(BaseModel):
    record_id: str

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# In-memory storage for demo (in production, this would be ServiceNow API)
records_storage = {}

@app.get("/meta")
async def get_metadata():
    """Get server metadata and capabilities"""
    return {
        "server_name": "servicenow",
        "version": "1.0.0", 
        "capabilities": ["create_record", "get_record"],
        "description": "ServiceNow ITSM integration for incident and task management",
        "authentication_required": True,
        "endpoints": {
            "create_record": {
                "method": "POST",
                "parameters": {
                    "type": "string",
                    "summary": "string", 
                    "description": "string",
                    "severity": "string (optional)",
                    "assigned_to": "string (optional)"
                },
                "description": "Create a new record (incident/task)"
            },
            "get_record": {
                "method": "POST",
                "parameters": {"record_id": "string"},
                "description": "Retrieve a record by ID"
            }
        }
    }

@app.post("/create_record", response_model=MCPResponse)
async def create_record(request: CreateRecordRequest, authorization: Optional[str] = Header(None)):
    """Create a new ServiceNow record"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        # Generate unique record ID
        record_id = f"INC{str(uuid.uuid4())[:8].upper()}"
        
        # Create record
        record = {
            "record_id": record_id,
            "type": request.type,
            "summary": request.summary,
            "description": request.description,
            "severity": request.severity,
            "assigned_to": request.assigned_to or "Unassigned",
            "status": "New",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "created_by": "MCP Agent"
        }
        
        # Store record
        records_storage[record_id] = record
        
        return MCPResponse(success=True, data=record)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/get_record", response_model=MCPResponse)
async def get_record(request: GetRecordRequest, authorization: Optional[str] = Header(None)):
    """Get a ServiceNow record by ID"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        record_id = request.record_id
        
        if record_id not in records_storage:
            return MCPResponse(success=False, error=f"Record {record_id} not found")
            
        record = records_storage[record_id]
        return MCPResponse(success=True, data=record)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.get("/records")
async def list_all_records():
    """List all records (for debugging)"""
    return {"records": list(records_storage.values())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
