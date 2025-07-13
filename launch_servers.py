
#!/usr/bin/env python3
"""
Launch all MCP servers for the cybersecurity application
"""

import subprocess
import sys
import time
import threading
from pathlib import Path

def launch_server(server_script, port, name):
    """Launch a single MCP server"""
    print(f"Starting {name} server on port {port}...")
    
    try:
        process = subprocess.Popen([
            sys.executable, server_script
        ], cwd=Path(__file__).parent)
        
        print(f"✓ {name} server started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"✗ Failed to start {name} server: {e}")
        return None

def main():
    """Launch all MCP servers"""
    
    servers = [
        ("src/servers/virustotal_server.py", 8001, "VirusTotal"),
        ("src/servers/servicenow_server.py", 8002, "ServiceNow"), 
        ("src/servers/cyberreason_server.py", 8003, "CyberReason"),
        ("src/servers/custom_rest_server.py", 8004, "Custom REST")
    ]
    
    processes = []
    
    print("🚀 Launching MCP Cybersecurity Servers...")
    print("=" * 50)
    
    for server_script, port, name in servers:
        process = launch_server(server_script, port, name)
        if process:
            processes.append((process, name))
        time.sleep(1)  # Brief delay between launches
        
    print("\n" + "=" * 50)
    print(f"✓ Started {len(processes)} servers")
    print("\nServer URLs:")
    for _, port, name in servers:
        print(f"  {name}: http://0.0.0.0:{port}")
        
    print("\nTo stop servers, press Ctrl+C")
    
    try:
        # Wait for servers to run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all servers...")
        for process, name in processes:
            try:
                process.terminate()
                print(f"✓ Stopped {name} server")
            except:
                pass
        print("All servers stopped.")

if __name__ == "__main__":
    main()
