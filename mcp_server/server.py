"""
FastMCP Server for Digital Clone App
Thin proxy layer that forwards tool calls to Ray Serve endpoints
"""

import aiohttp
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

from fastmcp import FastMCP

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Create the MCP server instance
mcp = FastMCP(name="digital-clone-mcp")

# Ray Serve tools server configuration
RAY_SERVE_URL = "http://localhost:8003"


async def _call_ray_serve_tool(endpoint: str, data: Dict[str, Any]) -> str:
    """
    Call a Ray Serve tool endpoint and return the result
    
    Args:
        endpoint: The tool endpoint (e.g., "web_search", "read_file")
        data: The request data
        
    Returns:
        str: Tool result or error message
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{RAY_SERVE_URL}/tools/{endpoint}"
            async with session.post(url, json=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("result", "")
                    else:
                        return f"Tool error: {result.get('error', 'Unknown error')}"
                else:
                    return f"HTTP error {response.status}: {await response.text()}"
    except Exception as e:
        return f"Error calling Ray Serve tool: {str(e)}"


@mcp.tool
def web_search(query: str) -> str:
    """
    Search the web for information using DuckDuckGo.
    
    Args:
        query: The search query to look up
        
    Returns:
        str: Search results or error message
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("web_search", {"query": query}))
    finally:
        loop.close()


@mcp.tool
def read_file(file_path: str) -> str:
    """
    Read contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        str: File contents or error message
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("read_file", {"file_path": file_path}))
    finally:
        loop.close()


@mcp.tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        str: Success message or error
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("write_file", {
            "file_path": file_path,
            "content": content
        }))
    finally:
        loop.close()


@mcp.tool
def list_directory(directory_path: str) -> str:
    """
    List contents of a directory.
    
    Args:
        directory_path: Path to the directory to list
        
    Returns:
        str: Directory listing or error message
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("list_directory", {"directory_path": directory_path}))
    finally:
        loop.close()


@mcp.tool
def calculate(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        str: Result or error message
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("calculate", {"expression": expression}))
    finally:
        loop.close()


@mcp.tool
def get_system_info() -> str:
    """
    Get current system information.
    
    Returns:
        str: System information
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("get_system_info", {}))
    finally:
        loop.close()


@mcp.tool
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio from a .wav file using OpenAI's Whisper API.
    
    Args:
        file_path: Path to the .wav audio file to transcribe
        
    Returns:
        str: Transcribed text or error message
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_call_ray_serve_tool("transcribe_audio", {"file_path": file_path}))
    finally:
        loop.close()


if __name__ == "__main__":
    # Run the MCP server with HTTP transport on localhost at port 8001
    print("🚀 Starting FastMCP Server for Digital Clone")
    print("📍 Port: 8001")
    print("🔧 Available tools: web_search, read_file, write_file, list_directory, calculate, get_system_info, transcribe_audio")
    print("🔗 Ray Serve Tools Server: http://localhost:8003")
    
    mcp.run(transport="http", host="127.0.0.1", port=8001) 