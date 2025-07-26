
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

class UpdateRecordRequest(BaseModel):
    table_name: str
    sys_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    state: Optional[str] = None
    comments: Optional[str] = None
    active: Optional[bool] = None

class DeleteRecordRequest(BaseModel):
    table_name: str
    sys_id: str

class RetrieveRecordRequest(BaseModel):
    table_name: str
    sys_id: str
    display_value: Optional[bool] = False
    fields: Optional[str] = None

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
        "capabilities": ["create_record", "get_record", "update_record", "delete_record", "retrieve_record"],
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
            },
            "update_record": {
                "method": "POST",
                "parameters": {
                    "table_name": "string",
                    "sys_id": "string",
                    "summary": "string (optional)",
                    "description": "string (optional)",
                    "severity": "string (optional)",
                    "assigned_to": "string (optional)"
                },
                "description": "Update an existing record"
            },
            "delete_record": {
                "method": "POST",
                "parameters": {
                    "table_name": "string",
                    "sys_id": "string"
                },
                "description": "Delete a record by sys_id"
            },
            "retrieve_record": {
                "method": "POST",
                "parameters": {
                    "table_name": "string",
                    "sys_id": "string",
                    "display_value": "boolean (optional)",
                    "fields": "string (optional)"
                },
                "description": "Retrieve a specific record with optional field filtering"
            }
        }
    }

@app.post("/create_record", response_model=MCPResponse)
async def create_record(request: CreateRecordRequest, authorization: Optional[str] = Header(None)):
    """Create a new ServiceNow record"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        # Generate unique record ID and sys_id
        record_id = f"INC{str(uuid.uuid4())[:8].upper()}"
        sys_id = str(uuid.uuid4())
        
        # Create record
        record = {
            "record_id": record_id,
            "sys_id": sys_id,
            "type": request.type,
            "summary": request.summary,
            "description": request.description,
            "severity": request.severity,
            "assigned_to": request.assigned_to or "Unassigned",
            "status": "New",
            "active": True,
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

@app.post("/update_record", response_model=MCPResponse)
async def update_record(request: UpdateRecordRequest, authorization: Optional[str] = Header(None)):
    """Update an existing ServiceNow record"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        # Generate a sys_id-like identifier for lookup
        record_id = request.sys_id
        
        # Find record by sys_id in stored records
        found_record = None
        for stored_id, record in records_storage.items():
            if record.get("sys_id") == record_id or stored_id == record_id:
                found_record = record
                break
        
        if not found_record:
            return MCPResponse(success=False, error=f"Record with sys_id {record_id} not found")
        
        # Update fields if provided
        if request.summary:
            found_record["summary"] = request.summary
        if request.description:
            found_record["description"] = request.description
        if request.severity:
            found_record["severity"] = request.severity
        if request.assigned_to:
            found_record["assigned_to"] = request.assigned_to
        if request.priority:
            found_record["priority"] = request.priority
        if request.state:
            found_record["state"] = request.state
        if request.comments:
            found_record["comments"] = request.comments
        if request.active is not None:
            found_record["active"] = request.active
            
        found_record["updated_at"] = datetime.datetime.now().isoformat()
        
        return MCPResponse(success=True, data=found_record)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/delete_record", response_model=MCPResponse)
async def delete_record(request: DeleteRecordRequest, authorization: Optional[str] = Header(None)):
    """Delete a ServiceNow record"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        record_id = request.sys_id
        
        # Find and remove record by sys_id
        found_key = None
        for stored_id, record in records_storage.items():
            if record.get("sys_id") == record_id or stored_id == record_id:
                found_key = stored_id
                break
        
        if not found_key:
            return MCPResponse(success=False, error=f"Record with sys_id {record_id} not found")
        
        deleted_record = records_storage.pop(found_key)
        
        return MCPResponse(
            success=True, 
            data={"message": f"Record {record_id} deleted successfully", "deleted_record": deleted_record}
        )
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/retrieve_record", response_model=MCPResponse)
async def retrieve_record(request: RetrieveRecordRequest, authorization: Optional[str] = Header(None)):
    """Retrieve a specific ServiceNow record with optional field filtering"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        record_id = request.sys_id
        
        # Find record by sys_id
        found_record = None
        for stored_id, record in records_storage.items():
            if record.get("sys_id") == record_id or stored_id == record_id:
                found_record = record.copy()
                break
        
        if not found_record:
            return MCPResponse(success=False, error=f"Record with sys_id {record_id} not found")
        
        # Apply field filtering if specified
        if request.fields:
            field_list = [field.strip() for field in request.fields.split(",")]
            filtered_record = {}
            for field in field_list:
                if field in found_record:
                    filtered_record[field] = found_record[field]
            found_record = filtered_record
        
        # Add display_value formatting if requested (simplified implementation)
        if request.display_value:
            # In a real implementation, this would format values for display
            found_record["_display_values"] = "Display value formatting enabled"
        
        return MCPResponse(success=True, data=found_record)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.get("/records")
async def list_all_records():
    """List all records (for debugging)"""
    return {"records": list(records_storage.values())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
