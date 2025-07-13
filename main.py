
#!/usr/bin/env python3
"""
AI-Driven Agentic Cybersecurity Application with MCP
Main entry point for the desktop application
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.client.desktop_app import CyberSecurityApp

def main():
    """Main entry point for the cybersecurity application"""
    app = CyberSecurityApp()
    app.run()

if __name__ == "__main__":
    main()
