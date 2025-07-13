#!/usr/bin/env python3
"""
Startup script for the Ray Serve Tools Server
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ray import serve
from tools_server.tools import tools_deployment


def main():
    """Main entry point"""
    print("🚀 Starting Ray Serve Tools Server")
    print("📍 Port: 8003")
    print("🔧 Available tools: web_search, read_file, write_file, list_directory, calculate, get_system_info, transcribe_audio")
    print("📊 Ray Serve Dashboard: http://localhost:8265")
    
    # Get port from environment or use default
    port = int(os.getenv("RAY_SERVE_PORT", "8003"))
    
    try:
        # Start Ray Serve
        serve.start(detached=True, http_options={"host": "0.0.0.0", "port": port})
        
        # Deploy the tools with route prefix
        serve.run(tools_deployment, route_prefix="/tools")
        
        print(f"✅ Ray Serve Tools Server started successfully on port {port}")
        print("🔗 Tools endpoints:")
        print(f"   - Web Search: http://localhost:{port}/tools/web_search")
        print(f"   - Read File: http://localhost:{port}/tools/read_file")
        print(f"   - Write File: http://localhost:{port}/tools/write_file")
        print(f"   - List Directory: http://localhost:{port}/tools/list_directory")
        print(f"   - Calculate: http://localhost:{port}/tools/calculate")
        print(f"   - System Info: http://localhost:{port}/tools/get_system_info")
        print(f"   - Transcribe Audio: http://localhost:{port}/tools/transcribe_audio")
        print(f"   - Health Check: http://localhost:{port}/tools/health")
        
        # Keep the server running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Ray Serve Tools Server stopped by user")
            serve.shutdown()
            
    except Exception as e:
        print(f"❌ Error starting Ray Serve Tools Server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 