"""
Data models for the LangGraph agent system
"""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """A message in the conversation"""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: List[Message]
    current_task: Optional[str]
    context: Dict[str, Any]
    agent_memory: Dict[str, Any]
    tools_results: List[Dict[str, Any]]
    conversation_id: str


class ToolResult(BaseModel):
    """Result from a tool execution"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationRequest(BaseModel):
    """Request for a conversation"""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for continuity")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class ConversationResponse(BaseModel):
    """Response from the conversation"""
    response: str = Field(..., description="Agent response")
    conversation_id: str = Field(..., description="Conversation ID")
    tools_used: List[str] = Field(default_factory=list, description="Tools used in this response")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AgentConfig(BaseModel):
    """Configuration for the agent"""
    model_name: str = Field(default="gpt-3.5-turbo", description="LLM model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens for response")
    system_prompt: str = Field(default="You are a helpful AI assistant.", description="System prompt")
    enable_tools: bool = Field(default=True, description="Whether to enable tool usage")
    mcp_server_url: str = Field(default="http://localhost:8001", description="MCP server URL") 