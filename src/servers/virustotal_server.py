
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
import asyncio
import aiohttp
import uvicorn
import hashlib
import re
import json
import base64

app = FastAPI(title="VirusTotal MCP Server", version="1.1.0")

# Request Models
class IPReportRequest(BaseModel):
    ip: str

class DomainReportRequest(BaseModel):
    domain: str

class HashLookupRequest(BaseModel):
    hashes: List[str]
    enable_raw_json: Optional[bool] = False
    
    @validator('hashes')
    def validate_hashes(cls, v):
        hash_pattern = re.compile(r'^[a-fA-F0-9]+$')
        for hash_val in v:
            if not hash_pattern.match(hash_val):
                raise ValueError(f'Invalid hash format: {hash_val}')
            if len(hash_val) not in [32, 40, 64]:  # MD5, SHA1, SHA256
                raise ValueError(f'Invalid hash length: {hash_val}')
        return v

class URLLookupRequest(BaseModel):
    urls: List[str]
    enable_raw_json: Optional[bool] = False

class DomainLookupRequest(BaseModel):
    domains: List[str]
    enable_raw_json: Optional[bool] = False

class IPLookupRequest(BaseModel):
    ip_addresses: List[str]
    enable_raw_json: Optional[bool] = False

class LookupIndicatorsRequest(BaseModel):
    domains: Optional[List[str]] = None
    hashes: Optional[List[str]] = None
    ip_addresses: Optional[List[str]] = None
    urls: Optional[List[str]] = None
    enable_raw_json: Optional[bool] = False
    force_scan: Optional[bool] = False
    max_resolutions: Optional[int] = 10

class FileAnalysisRequest(BaseModel):
    file_content: str  # Base64 encoded file content
    filename: Optional[str] = "unknown"
    enable_raw_json: Optional[bool] = False

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_code: Optional[int] = None

# Mock VirusTotal responses for demo
MOCK_RESPONSES = {
    "192.168.1.100": {
        "ip": "192.168.1.100",
        "reputation": "malicious",
        "threat_score": 85,
        "detections": 15,
        "total_engines": 20,
        "first_seen": "2024-01-15",
        "last_seen": "2024-01-20",
        "asn": 12345,
        "as_owner": "Malicious ISP",
        "country": "US",
        "detected_urls": [
            {"url": "http://192.168.1.100/malware.exe", "positives": 12, "total": 20}
        ]
    },
    "malicious-domain.com": {
        "domain": "malicious-domain.com", 
        "reputation": "malicious",
        "threat_score": 92,
        "categories": ["malware", "phishing"],
        "first_seen": "2024-01-10",
        "last_analysis": "2024-01-20",
        "alexa_rank": None,
        "detected_urls": [
            {"url": "http://malicious-domain.com/bad.exe", "positives": 18, "total": 20}
        ],
        "resolutions": ["192.168.1.100", "10.0.0.1"]
    },
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": {
        "hash": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
        "md5": "44d88612fea8a8f36de82e1278abb02f",
        "sha1": "0a3d92634bfdc0b84db1b6ff3b86c86b14ff2c1f",
        "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
        "reputation": "malicious",
        "positives": 45,
        "total": 69,
        "scan_date": "2024-01-20",
        "vendor_scans": {
            "Microsoft": {"detected": True, "result": "Trojan:Win32/Generic"},
            "Symantec": {"detected": True, "result": "Trojan.Gen.MBT"},
            "McAfee": {"detected": False, "result": None}
        }
    },
    "http://malicious-url.com/test": {
        "url": "http://malicious-url.com/test",
        "reputation": "malicious",
        "positives": 22,
        "total": 70,
        "scan_date": "2024-01-20",
        "response_code": 1
    }
}

def generate_mock_scan_report(indicator_type, indicators, enable_raw_json=False):
    """Generate mock scan reports for different indicator types"""
    results = []
    raw_data = []
    
    for indicator in indicators:
        if indicator in MOCK_RESPONSES:
            result = MOCK_RESPONSES[indicator].copy()
        else:
            # Generate clean response for unknown indicators
            if indicator_type == "hash":
                result = {
                    "hash": indicator,
                    "reputation": "clean",
                    "positives": 0,
                    "total": 69,
                    "scan_date": "2024-01-20",
                    "vendor_scans": {}
                }
            elif indicator_type == "domain":
                result = {
                    "domain": indicator,
                    "reputation": "clean",
                    "threat_score": 5,
                    "categories": ["legitimate"],
                    "alexa_rank": 1000,
                    "detected_urls": [],
                    "resolutions": []
                }
            elif indicator_type == "ip":
                result = {
                    "ip": indicator,
                    "reputation": "clean",
                    "threat_score": 10,
                    "detections": 0,
                    "total_engines": 20,
                    "asn": 12345,
                    "as_owner": "Clean ISP",
                    "country": "US",
                    "detected_urls": []
                }
            elif indicator_type == "url":
                result = {
                    "url": indicator,
                    "reputation": "clean",
                    "positives": 0,
                    "total": 70,
                    "scan_date": "2024-01-20",
                    "response_code": 1
                }
        
        results.append(result)
        if enable_raw_json:
            raw_data.append(result)
    
    scan_report = {
        "has_suspicious_object": any(r.get("reputation") == "malicious" for r in results),
        "white_list": [r.get(indicator_type, r.get("hash", r.get("url", ""))) 
                      for r in results if r.get("reputation") != "malicious"],
        "black_list": [r.get(indicator_type, r.get("hash", r.get("url", ""))) 
                      for r in results if r.get("reputation") == "malicious"],
        "status_msg": "Scan completed successfully",
        "scan_result": results
    }
    
    return raw_data if enable_raw_json else None, scan_report

@app.get("/meta")
async def get_metadata():
    """Get server metadata and capabilities"""
    return {
        "server_name": "virustotal",
        "version": "1.0.0",
        "capabilities": ["ip_report", "domain_report", "lookup_hashes", "lookup_urls", "lookup_domains", 
                       "lookup_ip_addresses", "lookup_indicators", "analyse_file"],
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
            },
            "lookup_hashes": {
                "method": "POST",
                "parameters": {
                    "hashes": "list of strings",
                    "enable_raw_json": "boolean (optional)"
                },
                "description": "Lookup file hashes for malware analysis"
            },
            "lookup_urls": {
                "method": "POST",
                "parameters": {
                    "urls": "list of strings",
                    "enable_raw_json": "boolean (optional)"
                },
                "description": "Lookup URLs for malicious content"
            },
            "lookup_domains": {
                "method": "POST",
                "parameters": {
                    "domains": "list of strings",
                    "enable_raw_json": "boolean (optional)"
                },
                "description": "Lookup domains for reputation analysis"
            },
            "lookup_ip_addresses": {
                "method": "POST",
                "parameters": {
                    "ip_addresses": "list of strings",
                    "enable_raw_json": "boolean (optional)"
                },
                "description": "Lookup IP addresses for threat intelligence"
            },
            "lookup_indicators": {
                "method": "POST",
                "parameters": {
                    "domains": "list of strings (optional)",
                    "hashes": "list of strings (optional)",
                    "ip_addresses": "list of strings (optional)",
                    "urls": "list of strings (optional)",
                    "force_scan": "boolean (optional)",
                    "max_resolutions": "integer (optional)"
                },
                "description": "Comprehensive lookup for multiple indicator types"
            },
            "analyse_file": {
                "method": "POST",
                "parameters": {
                    "file_content": "base64 encoded file",
                    "filename": "string (optional)",
                    "enable_raw_json": "boolean (optional)"
                },
                "description": "Upload and analyze file for malware detection"
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

@app.post("/lookup_hashes", response_model=MCPResponse)
async def lookup_hashes(request: HashLookupRequest, x_api_key: Optional[str] = Header(None)):
    """Lookup file hashes for malware analysis"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        raw_json, scan_report = generate_mock_scan_report("hash", request.hashes, request.enable_raw_json)
        
        response_data = {
            "hash_scan_report": scan_report,
            "task_success": True,
            "status_msg": "Hash lookup completed successfully"
        }
        
        if request.enable_raw_json and raw_json:
            response_data["raw_json"] = json.dumps(raw_json)
            
        return MCPResponse(success=True, data=response_data, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/lookup_urls", response_model=MCPResponse)
async def lookup_urls(request: URLLookupRequest, x_api_key: Optional[str] = Header(None)):
    """Lookup URLs for malicious content"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        raw_json, scan_report = generate_mock_scan_report("url", request.urls, request.enable_raw_json)
        
        response_data = {
            "url_scan_report": scan_report,
            "task_success": True,
            "status_msg": "URL lookup completed successfully"
        }
        
        if request.enable_raw_json and raw_json:
            response_data["raw_json"] = json.dumps(raw_json)
            
        return MCPResponse(success=True, data=response_data, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/lookup_domains", response_model=MCPResponse)
async def lookup_domains(request: DomainLookupRequest, x_api_key: Optional[str] = Header(None)):
    """Lookup domains for reputation analysis"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        raw_json, scan_report = generate_mock_scan_report("domain", request.domains, request.enable_raw_json)
        
        response_data = {
            "domain_scan_report": scan_report,
            "task_success": True,
            "status_msg": "Domain lookup completed successfully"
        }
        
        if request.enable_raw_json and raw_json:
            response_data["raw_json"] = json.dumps(raw_json)
            
        return MCPResponse(success=True, data=response_data, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/lookup_ip_addresses", response_model=MCPResponse)
async def lookup_ip_addresses(request: IPLookupRequest, x_api_key: Optional[str] = Header(None)):
    """Lookup IP addresses for threat intelligence"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        raw_json, scan_report = generate_mock_scan_report("ip", request.ip_addresses, request.enable_raw_json)
        
        response_data = {
            "ip_scan_report": scan_report,
            "task_success": True,
            "status_msg": "IP address lookup completed successfully"
        }
        
        if request.enable_raw_json and raw_json:
            response_data["raw_json"] = json.dumps(raw_json)
            
        return MCPResponse(success=True, data=response_data, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/lookup_indicators", response_model=MCPResponse)
async def lookup_indicators(request: LookupIndicatorsRequest, x_api_key: Optional[str] = Header(None)):
    """Comprehensive lookup for multiple indicator types"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        # Validate that at least one indicator type is provided
        if not any([request.domains, request.hashes, request.ip_addresses, request.urls]):
            raise HTTPException(status_code=400, detail="At least one indicator type is required")
        
        vt_lookup = {}
        all_raw_json = []
        
        # Process each indicator type
        if request.domains:
            raw_json, domain_report = generate_mock_scan_report("domain", request.domains, request.enable_raw_json)
            vt_lookup["domain_scan_report"] = domain_report
            if raw_json:
                all_raw_json.extend(raw_json)
        
        if request.hashes:
            raw_json, hash_report = generate_mock_scan_report("hash", request.hashes, request.enable_raw_json)
            vt_lookup["hash_scan_report"] = hash_report
            if raw_json:
                all_raw_json.extend(raw_json)
        
        if request.ip_addresses:
            raw_json, ip_report = generate_mock_scan_report("ip", request.ip_addresses, request.enable_raw_json)
            vt_lookup["ip_scan_report"] = ip_report
            if raw_json:
                all_raw_json.extend(raw_json)
        
        if request.urls:
            raw_json, url_report = generate_mock_scan_report("url", request.urls, request.enable_raw_json)
            vt_lookup["url_scan_report"] = url_report
            if raw_json:
                all_raw_json.extend(raw_json)
        
        response_data = {
            "vt_lookup": vt_lookup,
            "task_success": True,
            "status_msg": "Multi-indicator lookup completed successfully"
        }
        
        if request.enable_raw_json and all_raw_json:
            response_data["raw_json"] = json.dumps(all_raw_json)
            
        return MCPResponse(success=True, data=response_data, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.post("/analyse_file", response_model=MCPResponse)
async def analyse_file(request: FileAnalysisRequest, x_api_key: Optional[str] = Header(None)):
    """Upload and analyze file for malware detection"""
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        # Decode base64 file content
        try:
            file_data = base64.b64decode(request.file_content)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 file content")
        
        # Generate hash of the file for analysis
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Mock file analysis result
        analysis_result = {
            "file_scan_report": {
                "has_suspicious_object": False,
                "white_list": [file_hash],
                "black_list": [],
                "status_msg": f"File analysis completed for {request.filename}",
                "scan_result": [{
                    "hash": file_hash,
                    "filename": request.filename,
                    "file_size": len(file_data),
                    "reputation": "clean",
                    "positives": 0,
                    "total": 69,
                    "scan_date": "2024-01-20",
                    "vendor_scans": {
                        "Microsoft": {"detected": False, "result": "Clean"},
                        "Symantec": {"detected": False, "result": "Clean"},
                        "McAfee": {"detected": False, "result": "Clean"}
                    }
                }]
            },
            "task_success": True,
            "status_msg": "File analysis completed successfully"
        }
        
        # Check if file matches any known malicious patterns
        if file_hash in MOCK_RESPONSES:
            malicious_result = MOCK_RESPONSES[file_hash]
            analysis_result["file_scan_report"]["has_suspicious_object"] = True
            analysis_result["file_scan_report"]["black_list"] = [file_hash]
            analysis_result["file_scan_report"]["white_list"] = []
            analysis_result["file_scan_report"]["scan_result"] = [malicious_result]
        
        if request.enable_raw_json:
            analysis_result["raw_json"] = json.dumps(analysis_result["file_scan_report"]["scan_result"])
            
        return MCPResponse(success=True, data=analysis_result, response_code=200)
        
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
