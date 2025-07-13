#!/usr/bin/env python3
"""
Startup script for the FastMCP server
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the server directly
from mcp_server.server import mcp

if __name__ == "__main__":
    try:
        print("🚀 Starting FastMCP Server for Digital Clone")
        print("📍 Port: 8001")
        print("🔧 Available tools: web_search, read_file, write_file, list_directory, calculate, get_system_info, transcribe_audio")
        
        mcp.run(transport="http", host="127.0.0.1", port=8001)
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1) 