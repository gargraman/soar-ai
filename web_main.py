#!/usr/bin/env python3
"""
Main entry point for the web-based cybersecurity automation platform
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.client.web_app import WebSecurityApp

def main():
    """Main entry point for the web application"""
    print("Starting AI Cybersecurity Agent - Web Interface")
    print("=" * 50)
    
    # Create and run the web application
    web_app = WebSecurityApp()
    
    print("Web application starting on http://0.0.0.0:8080")
    print("Access the application in your browser at: http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        web_app.run(host="0.0.0.0", port=8080)
    except KeyboardInterrupt:
        print("\nShutting down web application...")
    except Exception as e:
        print(f"Error starting web application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()