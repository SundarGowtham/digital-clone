"""
LangGraph Multi-Agent System for Digital Clone
Uses local Ollama model (llama3:8b) and integrates with MCP server
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, TypedDict
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .models import (
    AgentState, Message, ToolResult, ConversationRequest, 
    ConversationResponse, AgentConfig
)
from .mcp_client import MCPClient, MockMCPClient


class DigitalCloneAgent:
    """Main agent class for the digital clone"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = Ollama(
            model="llama3:8b",
            temperature=config.temperature,
            base_url="http://localhost:11434"
        )
        self.mcp_client = MCPClient(config.mcp_server_url)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_message)
        workflow.add_node("plan", self._plan_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("update_memory", self._update_memory)
        
        # Define the workflow
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _analyze_message(self, state: AgentState) -> AgentState:
        """Analyze the user message and determine intent"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        if not last_message or last_message.role != "user":
            return state
        
        # Analyze the message content
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant that analyzes user messages to determine:
1. The user's intent
2. Whether tools are needed
3. The type of response required

Respond with a JSON object containing:
- intent: string (e.g., "question", "task", "conversation")
- needs_tools: boolean
- tool_requirements: list of required tools (if any)
- response_type: string (e.g., "informative", "action", "conversational")
- priority: string (e.g., "high", "medium", "low")
"""),
            ("user", "Analyze this message: {message}")
        ])
        
        chain = analysis_prompt | self.llm | JsonOutputParser()
        
        try:
            analysis = await chain.ainvoke({"message": last_message.content})
            state["context"]["analysis"] = analysis
            state["current_task"] = analysis.get("intent", "conversation")
        except Exception as e:
            # Fallback analysis
            state["context"]["analysis"] = {
                "intent": "conversation",
                "needs_tools": False,
                "tool_requirements": [],
                "response_type": "conversational",
                "priority": "medium"
            }
            state["current_task"] = "conversation"
        
        return state
    
    async def _plan_response(self, state: AgentState) -> AgentState:
        """Plan the response based on analysis"""
        analysis = state["context"].get("analysis", {})
        messages = state["messages"]
        
        planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant that plans responses. Based on the analysis, create a plan for responding to the user.

If tools are needed, specify which tools and how to use them.
If no tools are needed, plan a direct response.

Respond with a JSON object containing:
- plan: string (description of the plan)
- tools_to_use: list of tool names (if any)
- tool_arguments: dict of tool arguments (if any)
- response_strategy: string (how to structure the response)
"""),
            ("user", """Analysis: {analysis}
Messages: {messages}

Create a response plan.""")
        ])
        
        chain = planning_prompt | self.llm | JsonOutputParser()
        
        try:
            plan = await chain.ainvoke({
                "analysis": json.dumps(analysis),
                "messages": [msg.content for msg in messages[-3:]]  # Last 3 messages
            })
            state["context"]["plan"] = plan
        except Exception as e:
            # Fallback plan
            state["context"]["plan"] = {
                "plan": "Provide a helpful response",
                "tools_to_use": [],
                "tool_arguments": {},
                "response_strategy": "conversational"
            }
        
        return state
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute tools if needed"""
        plan = state["context"].get("plan", {})
        tools_to_use = plan.get("tools_to_use", [])
        tool_arguments = plan.get("tool_arguments", {})
        
        if not tools_to_use or not self.config.enable_tools:
            state["tools_results"] = []
            return state
        
        await self._ensure_mcp_client()
        results = await self._execute_tool_list(tools_to_use, tool_arguments)
        state["tools_results"] = results
        return state
    
    async def _ensure_mcp_client(self):
        """Ensure MCP client is available, fallback to mock if needed"""
        try:
            is_healthy = await self.mcp_client.health_check()
            if not is_healthy:
                print("MCP server not available, using mock client")
                self.mcp_client = MockMCPClient()
        except Exception:
            print("MCP server not available, using mock client")
            self.mcp_client = MockMCPClient()
    
    async def _execute_tool_list(self, tools_to_use: List[str], tool_arguments: Dict) -> List[Dict]:
        """Execute a list of tools"""
        results = []
        for tool_name in tools_to_use:
            result = await self._execute_single_tool(tool_name, tool_arguments.get(tool_name, {}))
            results.append(result)
        return results
    
    async def _execute_single_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a single tool"""
        try:
            result = await self.mcp_client.execute_tool(tool_name, **args)
            return {
                "tool": tool_name,
                "success": result.success,
                "result": result.result,
                "error": result.error
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "success": False,
                "result": None,
                "error": str(e)
            }
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate the final response"""
        context = self._build_response_context(state)
        lc_messages = self._convert_messages_to_langchain(state["messages"])
        
        try:
            response_content = await self._generate_response_content(context, lc_messages)
            response_message = self._create_response_message(response_content, state["tools_results"])
            state["messages"].append(response_message)
        except Exception as e:
            fallback_message = self._create_fallback_message(str(e))
            state["messages"].append(fallback_message)
        
        return state
    
    def _build_response_context(self, state: AgentState) -> str:
        """Build context for response generation"""
        context_parts = []
        analysis = state["context"].get("analysis", {})
        plan = state["context"].get("plan", {})
        tools_results = state["tools_results"]
        
        if analysis:
            context_parts.append(f"Intent: {analysis.get('intent', 'conversation')}")
        
        if plan:
            context_parts.append(f"Plan: {plan.get('plan', 'Provide helpful response')}")
        
        if tools_results:
            tools_summary = self._build_tools_summary(tools_results)
            context_parts.append(f"Tools used: {'; '.join(tools_summary)}")
        
        return "\n".join(context_parts) if context_parts else "No special context"
    
    def _build_tools_summary(self, tools_results: List[Dict]) -> List[str]:
        """Build summary of tools used"""
        summary = []
        for result in tools_results:
            if result["success"]:
                summary.append(f"{result['tool']}: Success")
            else:
                summary.append(f"{result['tool']}: Failed - {result['error']}")
        return summary
    
    def _convert_messages_to_langchain(self, messages: List[Message]) -> List:
        """Convert messages to LangChain format"""
        lc_messages = []
        for msg in messages[-5:]:  # Last 5 messages for context
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
        return lc_messages
    
    async def _generate_response_content(self, context: str, lc_messages: List) -> str:
        """Generate response content using LLM"""
        response_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a helpful AI assistant. Use the following context to provide a relevant and helpful response.

Context:
{context}

Respond naturally and conversationally. If tools were used, incorporate their results into your response.
If no tools were used, provide a helpful response based on the user's message."""),
            MessagesPlaceholder(variable_name="messages"),
            ("user", "Generate a helpful response based on the conversation and context.")
        ])
        
        chain = response_prompt | self.llm
        response = await chain.ainvoke({"messages": lc_messages})
        return response.content if hasattr(response, 'content') else str(response)
    
    def _create_response_message(self, content: str, tools_results: List[Dict]) -> Message:
        """Create response message"""
        tools_used = [r["tool"] for r in tools_results if r["success"]]
        return Message(
            role="assistant",
            content=content,
            metadata={"tools_used": tools_used}
        )
    
    def _create_fallback_message(self, error: str) -> Message:
        """Create fallback error message"""
        return Message(
            role="assistant",
            content="I apologize, but I encountered an error while processing your request. Please try again.",
            metadata={"error": error}
        )
    
    async def _update_memory(self, state: AgentState) -> AgentState:
        """Update agent memory with conversation context"""
        messages = state["messages"]
        
        # Extract key information for memory
        memory_update = {
            "last_interaction": datetime.now().isoformat(),
            "conversation_length": len(messages),
            "recent_topics": [],
            "tools_used": []
        }
        
        # Extract recent topics from messages
        recent_messages = messages[-3:]
        for msg in recent_messages:
            if msg.role == "user":
                # Simple keyword extraction (could be enhanced)
                words = msg.content.lower().split()
                memory_update["recent_topics"].extend(words[:5])  # First 5 words as topics
        
        # Track tools used
        for msg in messages:
            if msg.metadata and "tools_used" in msg.metadata:
                memory_update["tools_used"].extend(msg.metadata["tools_used"])
        
        state["agent_memory"].update(memory_update)
        return state
    
    async def process_message(self, request: ConversationRequest) -> ConversationResponse:
        """Process a user message and return a response"""
        state = await self._get_or_create_state(request)
        self._add_user_message(state, request)
        
        final_state = await self._process_through_graph(state)
        return self._create_response(final_state)
    
    async def _get_or_create_state(self, request: ConversationRequest) -> AgentState:
        """Get existing state or create new one"""
        if request.conversation_id:
            return await self._retrieve_or_create_state(request.conversation_id)
        else:
            conversation_id = str(uuid.uuid4())
            return self._create_initial_state(conversation_id)
    
    async def _retrieve_or_create_state(self, conversation_id: str) -> AgentState:
        """Try to retrieve existing state, create new if fails"""
        try:
            config = {"configurable": {"thread_id": conversation_id}}
            return await self.graph.aget_state(config)
        except:
            return self._create_initial_state(conversation_id)
    
    def _add_user_message(self, state: AgentState, request: ConversationRequest):
        """Add user message to state"""
        user_message = Message(
            role="user",
            content=request.message,
            metadata=request.context
        )
        state["messages"].append(user_message)
    
    async def _process_through_graph(self, state: AgentState) -> AgentState:
        """Process state through the graph"""
        config = {"configurable": {"thread_id": state["conversation_id"]}}
        return await self.graph.ainvoke(state, config)
    
    def _create_response(self, final_state: AgentState) -> ConversationResponse:
        """Create response from final state"""
        response_message = final_state["messages"][-1]
        tools_used = response_message.metadata.get("tools_used", []) if response_message.metadata else []
        
        return ConversationResponse(
            response=response_message.content,
            conversation_id=final_state["conversation_id"],
            tools_used=tools_used,
            metadata=response_message.metadata
        )
    
    def _create_initial_state(self, conversation_id: str) -> AgentState:
        """Create initial state for a new conversation"""
        return AgentState(
            messages=[
                Message(
                    role="system",
                    content=self.config.system_prompt
                )
            ],
            current_task=None,
            context={},
            agent_memory={},
            tools_results=[],
            conversation_id=conversation_id
        ) 