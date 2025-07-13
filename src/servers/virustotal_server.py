
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import uvicorn

app = FastAPI(title="VirusTotal MCP Server", version="1.0.0")

class IPReportRequest(BaseModel):
    ip: str

class DomainReportRequest(BaseModel):
    domain: str

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Mock VirusTotal responses for demo
MOCK_RESPONSES = {
    "192.168.1.100": {
        "ip": "192.168.1.100",
        "reputation": "malicious",
        "threat_score": 85,
        "detections": 15,
        "total_engines": 20,
        "first_seen": "2024-01-15",
        "last_seen": "2024-01-20"
    },
    "malicious-domain.com": {
        "domain": "malicious-domain.com", 
        "reputation": "malicious",
        "threat_score": 92,
        "categories": ["malware", "phishing"],
        "first_seen": "2024-01-10",
        "last_analysis": "2024-01-20"
    }
}

@app.get("/meta")
async def get_metadata():
    """Get server metadata and capabilities"""
    return {
        "server_name": "virustotal",
        "version": "1.0.0",
        "capabilities": ["ip_report", "domain_report"],
        "description": "VirusTotal reputation and threat intelligence",
        "authentication_required": True,
        "endpoints": {
            "ip_report": {
                "method": "POST",
                "parameters": {"ip": "string"},
                "description": "Get IP reputation report"
            },
            "domain_report": {
                "method": "POST", 
                "parameters": {"domain": "string"},
                "description": "Get domain reputation report"
            }
        }
    }

@app.post("/ip_report", response_model=MCPResponse)
async def get_ip_report(request: IPReportRequest, x_api_key: Optional[str] = Header(None)):
    """Get IP reputation report from VirusTotal"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        # In production, this would call the actual VirusTotal API
        # For demo, we use mock data
        ip = request.ip
        
        if ip in MOCK_RESPONSES:
            report = MOCK_RESPONSES[ip]
        else:
            # Default response for unknown IPs
            report = {
                "ip": ip,
                "reputation": "clean",
                "threat_score": 10,
                "detections": 0,
                "total_engines": 20,
                "first_seen": "unknown",
                "last_seen": "unknown"
            }
            
        return MCPResponse(success=True, data=report)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/domain_report", response_model=MCPResponse)
async def get_domain_report(request: DomainReportRequest, x_api_key: Optional[str] = Header(None)):
    """Get domain reputation report from VirusTotal"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        domain = request.domain
        
        if domain in MOCK_RESPONSES:
            report = MOCK_RESPONSES[domain]
        else:
            # Default response for unknown domains
            report = {
                "domain": domain,
                "reputation": "clean", 
                "threat_score": 5,
                "categories": ["uncategorized"],
                "first_seen": "unknown",
                "last_analysis": "unknown"
            }
            
        return MCPResponse(success=True, data=report)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
