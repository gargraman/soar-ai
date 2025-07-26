#!/usr/bin/env python3
"""
Test script for Trellix Cloud IVX MCP Server
"""

import asyncio
import aiohttp
import json

async def test_cloud_ivx_server():
    """Test all endpoints of the cloud_ivx server"""
    
    base_url = "http://localhost:8005"
    headers = {"X-API-Key": "test-api-key"}
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Get server metadata
        print("Testing /meta endpoint...")
        try:
            async with session.get(f"{base_url}/meta") as response:
                if response.status == 200:
                    meta_data = await response.json()
                    print("✓ Meta endpoint works")
                    print(f"  Server: {meta_data['server_name']} v{meta_data['version']}")
                    print(f"  Capabilities: {meta_data['capabilities']}")
                else:
                    print(f"✗ Meta endpoint failed: {response.status}")
        except Exception as e:
            print(f"✗ Meta endpoint error: {e}")
        
        print("\n" + "="*50)
        
        # Test 2: Hash lookup
        print("Testing hash lookup...")
        hash_payload = {
            "hashes": ["5d41402abc4b2a76b9719d911017c592", "098f6bcd4621d373cade4e832627b4f6"],
            "enable_raw_json": True
        }
        
        try:
            async with session.post(f"{base_url}/lookup_hashes", 
                                  json=hash_payload, 
                                  headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✓ Hash lookup works")
                    print(f"  Found {len(result['data']['hash_info'])} hash results")
                    for hash_info in result['data']['hash_info']:
                        print(f"    {hash_info['hash']}: {hash_info['verdict']}")
                else:
                    print(f"✗ Hash lookup failed: {response.status}")
        except Exception as e:
            print(f"✗ Hash lookup error: {e}")
        
        print("\n" + "="*50)
        
        # Test 3: Get report
        print("Testing get report...")
        report_payload = {
            "report_id": "550e8400-e29b-41d4-a716-446655440001",
            "include_all": True
        }
        
        try:
            async with session.post(f"{base_url}/get_report",
                                  json=report_payload,
                                  headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✓ Get report works")
                    report = result['data']['report']
                    print(f"  Report ID: {report['report_id']}")
                    print(f"  Verdict: {report['verdict']}")
                    print(f"  Threat: {report.get('threat_name', 'None')}")
                else:
                    print(f"✗ Get report failed: {response.status}")
        except Exception as e:
            print(f"✗ Get report error: {e}")
        
        print("\n" + "="*50)
        
        # Test 4: URL analysis
        print("Testing URL analysis...")
        url_payload = {
            "urls": ["http://suspicious-domain.com", "https://malware-site.net"]
        }
        
        try:
            async with session.post(f"{base_url}/analyse_url",
                                  json=url_payload,
                                  headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✓ URL analysis works")
                    print(f"  Report ID: {result['data']['report_id']}")
                    print(f"  URLs submitted: {result['data']['response_json']['urls_submitted']}")
                else:
                    print(f"✗ URL analysis failed: {response.status}")
        except Exception as e:
            print(f"✗ URL analysis error: {e}")
        
        print("\n" + "="*50)
        
        # Test 5: File analysis
        print("Testing file analysis...")
        file_payload = {
            "file_ref": "https://example.com/suspicious-file.exe"
        }
        
        try:
            async with session.post(f"{base_url}/analyse_file",
                                  json=file_payload,
                                  headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✓ File analysis works")
                    print(f"  Report ID: {result['data']['report_id']}")
                    response_json = json.loads(result['data']['response_json'])
                    print(f"  File type: {response_json['file_type']}")
                else:
                    print(f"✗ File analysis failed: {response.status}")
        except Exception as e:
            print(f"✗ File analysis error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Trellix Cloud IVX MCP Server")
    print("Make sure the server is running on port 8005")
    print("="*50)
    
    asyncio.run(test_cloud_ivx_server())
