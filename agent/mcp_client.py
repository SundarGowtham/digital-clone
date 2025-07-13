"""
MCP Client for communicating with the FastMCP server
"""

import asyncio
import json
import aiohttp
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .models import ToolResult


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]


class MCPClient:
    """Client for communicating with the FastMCP server"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_tools(self) -> List[MCPTool]:
        """Get available tools from the MCP server"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # FastMCP v2 uses /mcp endpoint to get tools
            async with self.session.get(f"{self.server_url}/mcp") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    return [MCPTool(**tool) for tool in tools_data]
                else:
                    print(f"Failed to get tools: {response.status}")
                    return []
        except Exception as e:
            print(f"Error getting tools: {e}")
            return []
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool on the MCP server"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # FastMCP v2 uses direct POST to /mcp/{tool_name}
            url = f"{self.server_url}/mcp/{tool_name}"
            
            async with self.session.post(
                url,
                json=kwargs,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result_text = await response.text()
                    return ToolResult(
                        tool_name=tool_name,
                        success=True,
                        result=result_text,
                        error=None
                    )
                else:
                    error_text = await response.text()
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        result=None,
                        error=f"HTTP {response.status}: {error_text}"
                    )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # FastMCP v2 uses /mcp endpoint for health check
            async with self.session.get(f"{self.server_url}/mcp") as response:
                return response.status == 200
        except Exception:
            return False


# Mock MCP client for testing when server is not available
class MockMCPClient(MCPClient):
    """Mock MCP client for testing"""
    
    async def get_tools(self) -> List[MCPTool]:
        """Return mock tools"""
        return [
            MCPTool(
                name="web_search",
                description="Search the web for information",
                parameters={"query": {"type": "string", "description": "Search query"}}
            ),
            MCPTool(
                name="read_file",
                description="Read contents of a file",
                parameters={"file_path": {"type": "string", "description": "Path to file"}}
            ),
            MCPTool(
                name="calculate",
                description="Safely evaluate mathematical expressions",
                parameters={"expression": {"type": "string", "description": "Mathematical expression"}}
            )
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Return mock tool results"""
        if tool_name == "web_search":
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=[{
                    "title": "Mock Search Result",
                    "url": "https://example.com",
                    "snippet": f"Mock search result for: {kwargs.get('query', '')}"
                }]
            )
        elif tool_name == "calculate":
            try:
                expression = kwargs.get("expression", "")
                result = eval(expression)
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result={"result": result, "expression": expression}
                )
            except Exception as e:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    error=str(e)
                )
        else:
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=f"Mock result for {tool_name}: {kwargs}"
            ) 