#!/usr/bin/env python3
"""
Startup script for the Digital Clone Agent API Server
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

from agent.api import AgentAPIServer
from agent.models import AgentConfig


def main():
    """Main entry point"""
    print("🤖 Starting Digital Clone Agent API Server")
    print("📍 Port: 8002")
    print("🧠 Model: llama3:8b (via Ollama)")
    print("🔗 MCP Server: http://localhost:8001")
    
    # Configuration
    config = AgentConfig(
        model_name="llama3:8b",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="You are a helpful AI assistant with access to various tools. You can search the web, read and write files, perform calculations, and get system information. Use these tools when they would be helpful to provide better responses.",
        enable_tools=True,
        mcp_server_url="http://localhost:8001"
    )
    
    server = AgentAPIServer(config)
    
    try:
        server.run(host="localhost", port=8002, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Agent API Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting agent API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 