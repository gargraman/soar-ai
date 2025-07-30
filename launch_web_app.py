#!/usr/bin/env python3
"""
Launch script for the web-based cybersecurity automation platform
Starts both MCP servers and the web application
"""

import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class WebAppLauncher:
    """Launcher for the complete web-based cybersecurity platform"""
    
    def __init__(self):
        self.processes = []
        self.shutdown_event = threading.Event()
        
        # MCP Server configurations
        self.mcp_servers = [
            {
                "name": "VirusTotal Server",
                "script": "src/servers/virustotal_server.py",
                "port": 8001
            },
            {
                "name": "ServiceNow Server", 
                "script": "src/servers/servicenow_server.py",
                "port": 8002
            },
            {
                "name": "CyberReason Server",
                "script": "src/servers/cyberreason_server.py", 
                "port": 8003
            },
            {
                "name": "Custom REST Server",
                "script": "src/servers/custom_rest_server.py",
                "port": 8004
            },
            {
                "name": "Cloud IVX Server",
                "script": "src/servers/cloud_ivx_server.py",
                "port": 8005
            }
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.shutdown_event.set()
        self.stop_all_processes()
        sys.exit(0)
    
    def start_mcp_servers(self):
        """Start all MCP servers"""
        print("Starting MCP servers...")
        print("-" * 40)
        
        for server in self.mcp_servers:
            try:
                print(f"Starting {server['name']} on port {server['port']}...")
                
                process = subprocess.Popen(
                    [sys.executable, server['script']],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=Path(__file__).parent
                )
                
                self.processes.append({
                    'name': server['name'],
                    'process': process,
                    'port': server['port']
                })
                
                print(f"✓ {server['name']} started (PID: {process.pid})")
                
            except Exception as e:
                print(f"✗ Failed to start {server['name']}: {e}")
        
        print(f"\nStarted {len(self.processes)} MCP servers")
        
        # Wait a moment for servers to initialize
        print("Waiting for servers to initialize...")
        time.sleep(3)
    
    def start_web_app(self):
        """Start the web application"""
        print("\nStarting Web Application...")
        print("-" * 40)
        
        try:
            print("Starting Web Interface on port 8080...")
            
            process = subprocess.Popen(
                [sys.executable, "web_main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=Path(__file__).parent,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append({
                'name': 'Web Application',
                'process': process,
                'port': 8080
            })
            
            print(f"✓ Web Application started (PID: {process.pid})")
            print(f"✓ Access the application at: http://localhost:8080")
            
            return process
            
        except Exception as e:
            print(f"✗ Failed to start Web Application: {e}")
            return None
    
    def monitor_processes(self):
        """Monitor running processes and restart if needed"""
        while not self.shutdown_event.is_set():
            for proc_info in self.processes[:]:  # Copy list to avoid modification during iteration
                process = proc_info['process']
                
                if process.poll() is not None:  # Process has terminated
                    print(f"⚠ {proc_info['name']} has stopped unexpectedly")
                    self.processes.remove(proc_info)
                    
                    # Attempt to restart (optional)
                    # self.restart_process(proc_info)
            
            time.sleep(5)  # Check every 5 seconds
    
    def stop_all_processes(self):
        """Stop all running processes"""
        print("\nStopping all processes...")
        
        for proc_info in self.processes:
            try:
                process = proc_info['process']
                name = proc_info['name']
                
                if process.poll() is None:  # Process is still running
                    print(f"Stopping {name}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        print(f"✓ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        print(f"⚠ Force killing {name}...")
                        process.kill()
                        process.wait()
                        print(f"✓ {name} force stopped")
                        
            except Exception as e:
                print(f"✗ Error stopping {proc_info['name']}: {e}")
        
        self.processes.clear()
        print("All processes stopped")
    
    def show_status(self):
        """Show status of all processes"""
        print("\nProcess Status:")
        print("-" * 50)
        
        for proc_info in self.processes:
            process = proc_info['process']
            name = proc_info['name']
            port = proc_info['port']
            
            if process.poll() is None:
                status = "Running"
                color = "✓"
            else:
                status = "Stopped"
                color = "✗"
            
            print(f"{color} {name:<25} Port: {port:<6} Status: {status}")
        
        if self.processes:
            print(f"\nWeb Interface: http://localhost:8080")
            print("MCP Server Status: http://localhost:8001/docs (and ports 8002-8005)")
    
    def run(self):
        """Main run method"""
        print("AI Cybersecurity Agent - Web Platform Launcher")
        print("=" * 60)
        
        try:
            # Start MCP servers first
            self.start_mcp_servers()
            
            # Start web application
            web_process = self.start_web_app()
            
            if not web_process:
                print("Failed to start web application, exiting...")
                self.stop_all_processes()
                return
            
            # Show current status
            self.show_status()
            
            print("\n" + "=" * 60)
            print("All services started successfully!")
            print("Access the web interface at: http://localhost:8080")
            print("Press Ctrl+C to stop all services")
            print("=" * 60)
            
            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # Stream web app output
            if web_process:
                try:
                    for line in web_process.stdout:
                        if not self.shutdown_event.is_set():
                            print(f"[WebApp] {line.strip()}")
                except:
                    pass
            
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Error during startup: {e}")
        finally:
            self.stop_all_processes()

def main():
    """Main entry point"""
    launcher = WebAppLauncher()
    launcher.run()

if __name__ == "__main__":
    main()