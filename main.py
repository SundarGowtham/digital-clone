#!/usr/bin/env python3
"""
Digital Clone App - Main Entry Point
A conversational AI system with MCP server and LangGraph agent
"""

import asyncio
import subprocess
import sys
import time
import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


def print_banner():
    """Print the application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🤖 DIGITAL CLONE APP 🤖                    ║
    ║                                                              ║
    ║  A conversational AI system with:                            ║
    ║  • FastMCP Server (Port 8001) - Tools & External APIs       ║
    ║  • LangGraph Agent (Port 8002) - Multi-agentic AI           ║
    ║  • Local Ollama Model (llama3:8b) - Privacy-focused AI      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_ollama():
    """Check if Ollama is running and has the required model"""
    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start Ollama first:")
            print("   ollama serve")
            return False
        
        # Check if llama3:8b model is available
        if "llama3:8b" not in result.stdout:
            print("⚠️  llama3:8b model not found. Please pull it:")
            print("   ollama pull llama3:8b")
            return False
        
        print("✅ Ollama is running with llama3:8b model")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        print("Please ensure Ollama is installed and running")
        return False


def start_ray_serve_tools():
    """Start the Ray Serve tools server"""
    print("\n🚀 Starting Ray Serve Tools Server...")
    try:
        process = subprocess.Popen([
            sys.executable, "tools_server/run.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Ray Serve Tools Server started successfully on port 8003")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start Ray Serve tools server: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Ray Serve tools server: {e}")
        return None


def start_mcp_server():
    """Start the MCP server"""
    print("\n🚀 Starting FastMCP Server...")
    try:
        process = subprocess.Popen([
            sys.executable, "mcp_server/run.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ MCP Server started successfully on port 8001")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start MCP server: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        return None


def start_agent_server():
    """Start the agent API server"""
    print("\n🤖 Starting Digital Clone Agent API Server...")
    try:
        process = subprocess.Popen([
            sys.executable, "agent/run.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Agent API Server started successfully on port 8002")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start agent server: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting agent server: {e}")
        return None


def show_usage():
    """Show usage information"""
    usage = """
    📖 USAGE:
    
    1. Start both servers:
       python main.py start
    
    2. Start only Ray Serve tools server:
       python main.py ray
    
    3. Start only MCP server:
       python main.py mcp
    
    4. Start only agent server:
       python main.py agent
    
    5. Test the system:
       python main.py test
    
    🔧 API ENDPOINTS:
    
    Ray Serve Tools Server (Port 8003):
    - POST /tools/web_search - Web search
    - POST /tools/read_file - Read file contents
    - POST /tools/write_file - Write file contents
    - POST /tools/list_directory - List directory contents
    - POST /tools/calculate - Mathematical calculations
    - POST /tools/get_system_info - System information
    - POST /tools/transcribe_audio - Audio transcription
    - GET /tools/health - Health check
    
    MCP Server (Port 8001):
    - Tools: web_search, read_file, write_file, list_directory, calculate, get_system_info, transcribe_audio
    
    Agent API (Port 8002):
    - POST /chat - Send messages to the AI
    - GET /health - Health check
    - GET /config - Get agent configuration
    - PUT /config - Update agent configuration
    - GET /tools - Get available tools
    
    📝 EXAMPLE USAGE:
    
    # Send a message to the AI
    curl -X POST http://localhost:8002/chat \\
         -H "Content-Type: application/json" \\
         -d '{"message": "Hello, can you help me search for information about AI?"}'
    
    # Check agent health
    curl http://localhost:8002/health
    
    # Get available tools
    curl http://localhost:8002/tools
    """
    print(usage)


def test_system():
    """Test the system by sending a sample message"""
    import requests
    
    print("\n🧪 Testing the Digital Clone system...")
    
    if not test_agent_health():
        return
    
    test_chat_message()


def test_agent_health():
    """Test agent health endpoint"""
    import requests
    
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ Agent API is healthy")
            return True
        else:
            print(f"❌ Agent API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to agent API: {e}")
        return False


def test_chat_message():
    """Test sending a chat message"""
    import requests
    
    test_message = {
        "message": "Hello! Can you tell me what tools you have available and help me calculate 15 * 23?"
    }
    
    try:
        response = requests.post(
            "http://localhost:8002/chat",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test message sent successfully!")
            print(f"🤖 AI Response: {result['response']}")
            print(f"🔧 Tools used: {result['tools_used']}")
            print(f"🆔 Conversation ID: {result['conversation_id']}")
        else:
            print(f"❌ Test message failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing system: {e}")


def main():
    """Main entry point"""
    print_banner()
    
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    command_handlers = {
        "start": handle_start_command,
        "ray": handle_ray_command,
        "mcp": handle_mcp_command,
        "agent": handle_agent_command,
        "test": handle_test_command
    }
    
    handler = command_handlers.get(command)
    if handler:
        handler()
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()


def handle_start_command():
    """Handle the start command"""
    if not check_ollama():
        return
    
    # Start Ray Serve tools server first
    ray_process = start_ray_serve_tools()
    if not ray_process:
        return
    
    # Start MCP server
    mcp_process = start_mcp_server()
    if not mcp_process:
        ray_process.terminate()
        return
    
    # Start agent server
    agent_process = start_agent_server()
    if not agent_process:
        ray_process.terminate()
        mcp_process.terminate()
        return
    
    run_servers(ray_process, mcp_process, agent_process)


def handle_ray_command():
    """Handle the Ray Serve tools server command"""
    ray_process = start_ray_serve_tools()
    if ray_process:
        run_single_server(ray_process, "Ray Serve tools server")


def handle_mcp_command():
    """Handle the MCP server command"""
    if not check_ollama():
        return
    
    mcp_process = start_mcp_server()
    if mcp_process:
        run_single_server(mcp_process, "MCP server")


def handle_agent_command():
    """Handle the agent server command"""
    if not check_ollama():
        return
    
    agent_process = start_agent_server()
    if agent_process:
        run_single_server(agent_process, "Agent server")


def handle_test_command():
    """Handle the test command"""
    test_system()


def run_servers(ray_process, mcp_process, agent_process):
    """Run all servers and monitor them"""
    print("\n🎉 Digital Clone App is running!")
    print("📍 Ray Serve Tools: http://localhost:8003")
    print("📍 MCP Server: http://localhost:8001")
    print("📍 Agent API: http://localhost:8002")
    print("📍 Ray Serve Dashboard: http://localhost:8265")
    print("\nPress Ctrl+C to stop all servers...")
    
    try:
        monitor_processes(ray_process, mcp_process, agent_process)
    except KeyboardInterrupt:
        stop_servers(ray_process, mcp_process, agent_process)


def run_single_server(process, server_name):
    """Run a single server and monitor it"""
    print(f"\nPress Ctrl+C to stop {server_name}...")
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print(f"\n✅ {server_name} stopped")


def monitor_processes(ray_process, mcp_process, agent_process):
    """Monitor all processes for unexpected termination"""
    while True:
        time.sleep(1)
        if ray_process.poll() is not None:
            print("❌ Ray Serve Tools Server stopped unexpectedly")
            break
        if mcp_process.poll() is not None:
            print("❌ MCP Server stopped unexpectedly")
            break
        if agent_process.poll() is not None:
            print("❌ Agent Server stopped unexpectedly")
            break


def stop_servers(ray_process, mcp_process, agent_process):
    """Stop all servers gracefully"""
    print("\n👋 Stopping servers...")
    ray_process.terminate()
    mcp_process.terminate()
    agent_process.terminate()
    print("✅ All servers stopped")


if __name__ == "__main__":
    main()
