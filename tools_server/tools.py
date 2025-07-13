"""
Ray Serve Tools Implementation
All tool functions converted to Ray Serve endpoints
"""

import aiohttp
import platform
import sys
import os
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ray import serve
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Create FastAPI app for Ray Serve
app = FastAPI(title="Digital Clone Tools Server", version="0.1.0")


class ToolRequest(BaseModel):
    """Base model for tool requests"""
    pass


class WebSearchRequest(ToolRequest):
    """Request model for web search"""
    query: str


class FileRequest(ToolRequest):
    """Request model for file operations"""
    file_path: str


class WriteFileRequest(ToolRequest):
    """Request model for write file operation"""
    file_path: str
    content: str


class DirectoryRequest(ToolRequest):
    """Request model for directory operations"""
    directory_path: str


class CalculateRequest(ToolRequest):
    """Request model for calculation"""
    expression: str


class TranscribeRequest(ToolRequest):
    """Request model for audio transcription"""
    file_path: str


class ToolResponse(BaseModel):
    """Response model for all tools"""
    result: str
    success: bool
    error: str = None


@serve.deployment(num_replicas=2, )
@serve.ingress(app)
class ToolsServer:
    """Ray Serve deployment for all tools"""
    
    def __init__(self):
        """Initialize the tools server"""
        pass
    
    @app.post("/web_search", response_model=ToolResponse)
    async def web_search(self, request: WebSearchRequest) -> ToolResponse:
        """Search the web for information using DuckDuckGo"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": request.query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        if data.get("Abstract"):
                            results.append(f"Abstract: {data.get('Abstract', '')}")
                        
                        for topic in data.get("RelatedTopics", [])[:3]:
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append(f"Related: {topic.get('Text', '')}")
                        
                        result = "\n\n".join(results) if results else "No results found."
                        return ToolResponse(result=result, success=True)
                    else:
                        return ToolResponse(
                            result="",
                            success=False,
                            error=f"Search failed with status {response.status}"
                        )
                        
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Search error: {str(e)}"
            )
    
    @app.post("/read_file", response_model=ToolResponse)
    async def read_file(self, request: FileRequest) -> ToolResponse:
        """Read contents of a file"""
        try:
            path = Path(request.file_path)
            if not path.exists():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"File not found: {request.file_path}"
                )
            
            if not path.is_file():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"Path is not a file: {request.file_path}"
                )
            
            content = path.read_text(encoding='utf-8')
            result = f"File contents ({len(content)} characters):\n\n{content}"
            return ToolResponse(result=result, success=True)
            
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Error reading file: {str(e)}"
            )
    
    @app.post("/write_file", response_model=ToolResponse)
    async def write_file(self, request: WriteFileRequest) -> ToolResponse:
        """Write content to a file"""
        try:
            path = Path(request.file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(request.content, encoding='utf-8')
            
            result = f"Successfully wrote {len(request.content)} characters to {request.file_path}"
            return ToolResponse(result=result, success=True)
            
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Error writing file: {str(e)}"
            )
    
    @app.post("/list_directory", response_model=ToolResponse)
    async def list_directory(self, request: DirectoryRequest) -> ToolResponse:
        """List contents of a directory"""
        try:
            path = Path(request.directory_path)
            if not path.exists():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"Directory not found: {request.directory_path}"
                )
            
            if not path.is_dir():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"Path is not a directory: {request.directory_path}"
                )
            
            items = []
            for item in path.iterdir():
                item_type = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else "-"
                items.append(f"{item_type:4} {size:>8} {item.name}")
            
            result = f"Directory listing for {request.directory_path}:\n\n" + "\n".join(items)
            return ToolResponse(result=result, success=True)
            
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Error listing directory: {str(e)}"
            )
    
    @app.post("/calculate", response_model=ToolResponse)
    async def calculate(self, request: CalculateRequest) -> ToolResponse:
        """Safely evaluate mathematical expressions"""
        try:
            # Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in request.expression):
                return ToolResponse(
                    result="",
                    success=False,
                    error="Expression contains unsafe characters"
                )
            
            result = eval(request.expression)
            return ToolResponse(result=f"Result: {result}", success=True)
            
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Calculation error: {str(e)}"
            )
    
    @app.post("/get_system_info", response_model=ToolResponse)
    async def get_system_info(self) -> ToolResponse:
        """Get current system information"""
        try:
            info = {
                "platform": platform.platform(),
                "python_version": sys.version,
                "current_time": datetime.now().isoformat(),
                "working_directory": str(Path.cwd())
            }
            
            result = "\n".join([f"{k}: {v}" for k, v in info.items()])
            return ToolResponse(result=result, success=True)
            
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Error getting system info: {str(e)}"
            )
    
    @app.post("/transcribe_audio", response_model=ToolResponse)
    async def transcribe_audio(self, request: TranscribeRequest) -> ToolResponse:
        """Transcribe audio from a .wav file using OpenAI's Whisper API"""
        try:
            # Check if file exists
            path = Path(request.file_path)
            if not path.exists():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"Audio file not found: {request.file_path}"
                )
            
            if not path.is_file():
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"Path is not a file: {request.file_path}"
                )
            
            # Check if it's a .wav file
            if path.suffix.lower() != '.wav':
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"File must be a .wav file, got: {path.suffix}"
                )
            
            # Check file size (Whisper has limits)
            file_size = path.stat().st_size
            max_size = 25 * 1024 * 1024  # 25MB limit
            if file_size > max_size:
                return ToolResponse(
                    result="",
                    success=False,
                    error=f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is 25MB."
                )
            
            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return ToolResponse(
                    result="",
                    success=False,
                    error="OPENAI_API_KEY environment variable not set"
                )
            
            # Read and encode the audio file
            with open(path, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare the request to OpenAI Whisper API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "whisper-1",
                "file": f"data:audio/wav;base64,{audio_base64}",
                "response_format": "text"
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.text()
                        return ToolResponse(result=result, success=True)
                    else:
                        error_text = await response.text()
                        return ToolResponse(
                            result="",
                            success=False,
                            error=f"Error from OpenAI API (status {response.status}): {error_text}"
                        )
                        
        except Exception as e:
            return ToolResponse(
                result="",
                success=False,
                error=f"Error transcribing audio: {str(e)}"
            )
    
    @app.get("/health")
    async def health_check(self):
        """Health check endpoint"""
        return {"status": "healthy", "service": "tools-server"}


# Create the deployment
tools_deployment = ToolsServer.bind() 