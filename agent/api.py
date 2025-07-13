"""
Flask REST API for the Digital Clone Agent
Wraps the LangGraph agent and provides HTTP endpoints
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from dotenv import load_dotenv

from .models import ConversationRequest, ConversationResponse, AgentConfig
from .graph import DigitalCloneAgent

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class AgentAPIServer:
    """Flask API server for the digital clone agent"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.agent = DigitalCloneAgent(self.config)
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        self._setup_health_route()
        self._setup_chat_route()
        self._setup_conversation_route()
        self._setup_config_routes()
        self._setup_tools_route()
    
    def _setup_health_route(self):
        """Setup health check route"""
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_config": {
                    "model": "llama3:8b",
                    "temperature": self.config.temperature,
                    "enable_tools": self.config.enable_tools
                }
            })
    
    def _setup_chat_route(self):
        """Setup chat route"""
        @self.app.route('/chat', methods=['POST'])
        def chat():
            """Main chat endpoint"""
            return self._handle_chat_request()
    
    def _setup_conversation_route(self):
        """Setup conversation route"""
        @self.app.route('/conversations/<conversation_id>', methods=['GET'])
        def get_conversation(conversation_id):
            """Get conversation history"""
            return self._handle_get_conversation(conversation_id)
    
    def _setup_config_routes(self):
        """Setup configuration routes"""
        @self.app.route('/config', methods=['GET'])
        def get_config():
            """Get current agent configuration"""
            return self._handle_get_config()
        
        @self.app.route('/config', methods=['PUT'])
        def update_config():
            """Update agent configuration"""
            return self._handle_update_config()
    
    def _setup_tools_route(self):
        """Setup tools route"""
        @self.app.route('/tools', methods=['GET'])
        def get_available_tools():
            """Get available tools from MCP server"""
            return self._handle_get_tools()
    
    def _handle_chat_request(self):
        """Handle chat request"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            chat_request = self._validate_chat_request(data)
            response = self._process_chat_message(chat_request)
            
            return jsonify({
                "response": response.response,
                "conversation_id": response.conversation_id,
                "tools_used": response.tools_used,
                "metadata": response.metadata,
                "timestamp": datetime.now().isoformat()
            })
            
        except ValidationError as e:
            return jsonify({"error": f"Validation error: {e.errors()}"}), 400
        except Exception as e:
            return jsonify({
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def _validate_chat_request(self, data):
        """Validate chat request data"""
        return ConversationRequest(**data)
    
    def _process_chat_message(self, chat_request):
        """Process chat message asynchronously"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.agent.process_message(chat_request))
        finally:
            loop.close()
    
    def _handle_get_conversation(self, conversation_id):
        """Handle get conversation request"""
        try:
            return jsonify({
                "conversation_id": conversation_id,
                "message": "Conversation history retrieval not implemented yet",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "error": f"Error retrieving conversation: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def _handle_get_config(self):
        """Handle get config request"""
        return jsonify({
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "system_prompt": self.config.system_prompt,
            "enable_tools": self.config.enable_tools,
            "mcp_server_url": self.config.mcp_server_url
        })
    
    def _handle_update_config(self):
        """Handle update config request"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            self._update_config_fields(data)
            self.agent = DigitalCloneAgent(self.config)
            
            return jsonify({
                "message": "Configuration updated successfully",
                "config": self._get_config_dict(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                "error": f"Error updating configuration: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def _update_config_fields(self, data):
        """Update config fields from request data"""
        allowed_fields = ['temperature', 'max_tokens', 'system_prompt', 'enable_tools']
        for field in allowed_fields:
            if field in data:
                setattr(self.config, field, data[field])
    
    def _get_config_dict(self):
        """Get config as dictionary"""
        return {
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "system_prompt": self.config.system_prompt,
            "enable_tools": self.config.enable_tools,
            "mcp_server_url": self.config.mcp_server_url
        }
    
    def _handle_get_tools(self):
        """Handle get tools request"""
        try:
            tools = self._get_available_tools_list()
            return jsonify({
                "tools": tools,
                "count": len(tools),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "error": f"Error retrieving tools: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def _get_available_tools_list(self):
        """Get list of available tools"""
        return [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {"query": {"type": "string", "description": "Search query"}}
            },
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {"file_path": {"type": "string", "description": "Path to file"}}
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "Content to write"}
                }
            },
            {
                "name": "list_directory",
                "description": "List contents of a directory",
                "parameters": {"directory_path": {"type": "string", "description": "Path to directory"}}
            },
            {
                "name": "calculate",
                "description": "Safely evaluate mathematical expressions",
                "parameters": {"expression": {"type": "string", "description": "Mathematical expression"}}
            },
            {
                "name": "get_system_info",
                "description": "Get current system information",
                "parameters": {}
            },
            {
                "name": "transcribe_audio",
                "description": "Transcribe audio from a .wav file using OpenAI's Whisper API",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to the .wav audio file"}
                }
            }
        ]
    
    def run(self, host: str = "localhost", port: int = 8002, debug: bool = False):
        """Run the Flask server"""
        print(f"Starting Digital Clone Agent API server on {host}:{port}")
        print(f"Using Ollama model: llama3:8b")
        print(f"MCP server URL: {self.config.mcp_server_url}")
        print(f"Tools enabled: {self.config.enable_tools}")
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point for the API server"""
    # Load configuration from environment variables
    config = AgentConfig(
        model_name=os.getenv("AGENT_MODEL", "llama3:8b"),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "1000")),
        system_prompt=os.getenv("AGENT_SYSTEM_PROMPT", "You are a helpful AI assistant."),
        enable_tools=os.getenv("AGENT_ENABLE_TOOLS", "true").lower() == "true",
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    )
    
    server = AgentAPIServer(config)
    server.run(debug=True)


if __name__ == "__main__":
    main() 