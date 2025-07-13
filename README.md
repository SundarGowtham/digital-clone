# 🤖 Digital Clone App

A conversational AI system with local Ollama model, FastMCP server, and LangGraph multi-agent architecture.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │  LangGraph      │    │  FastMCP        │    │  Ray Serve      │
│   (Port 3000)   │◄──►│  Agent API      │◄──►│  Server         │◄──►│  Tools Server   │
│                 │    │  (Port 8002)    │    │  (Port 8001)    │    │  (Port 8003)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Ollama         │
                       │  (llama3:8b)    │
                       │  (Port 11434)   │
                       └─────────────────┘
```

## ✨ Features

- **Local AI Model**: Uses Ollama with llama3:8b for privacy-focused AI
- **Multi-Agent System**: LangGraph-based stateful conversation management
- **Scalable Tools**: Ray Serve-powered tool execution with distributed processing
- **Tool Integration**: FastMCP server with web search, file operations, calculations, audio transcription
- **Modern UI**: Beautiful conversational interface with voice input support
- **REST API**: Clean HTTP endpoints for integration
- **Stateful Conversations**: Maintains conversation context across sessions

## 🛠️ Prerequisites

1. **Python 3.10+**
2. **Ollama** - [Install Ollama](https://ollama.ai/)
3. **llama3:8b model** - Pull with `ollama pull llama3:8b`
4. **OpenAI API Key** - For Whisper audio transcription (optional)

## 🔐 Environment Setup

Create a `.env` file in the project root with your configuration:

```bash
# Copy and modify the example
cp .env.example .env

# Or create manually:
cat > .env << EOF
# OpenAI API Key (required for Whisper transcription)
OPENAI_API_KEY=your_openai_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Server Configuration
MCP_SERVER_PORT=8001
AGENT_API_PORT=8002
AGENT_API_HOST=localhost

# Agent Configuration
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096
AGENT_ENABLE_TOOLS=true

# MCP Server Configuration
MCP_SERVER_HOST=127.0.0.1

# Optional: Logging Configuration
LOG_LEVEL=INFO
EOF
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Or install manually
pip install fastmcp langgraph langchain langchain-openai flask flask-cors pydantic python-dotenv requests websockets asyncio-mqtt aiohttp uvicorn fastapi pydantic-settings
```

### 2. Start Ollama

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the model (if not already done)
ollama pull llama3:8b
```

### 3. Start the Digital Clone System

```bash
# Start all servers (Ray Serve, MCP, Agent)
python main.py start

# Or start components individually:
python main.py ray    # Start only Ray Serve tools server
python main.py mcp    # Start only MCP server
python main.py agent  # Start only agent API
```

### 4. Access the UI

Open `ui/index.html` in your browser or serve it with a local server:

```bash
# Using Python
python -m http.server 3000

# Then visit: http://localhost:3000/ui/
```

## 📡 API Endpoints

### Ray Serve Tools Server (Port 8003)

- `POST /tools/web_search` - Web search using DuckDuckGo
- `POST /tools/read_file` - Read file contents
- `POST /tools/write_file` - Write file contents
- `POST /tools/list_directory` - List directory contents
- `POST /tools/calculate` - Mathematical calculations
- `POST /tools/get_system_info` - System information
- `POST /tools/transcribe_audio` - Audio transcription using OpenAI Whisper
- `GET /tools/health` - Health check

### Agent API (Port 8002)

- `POST /chat` - Send messages to the AI
- `GET /health` - Health check
- `GET /config` - Get agent configuration
- `PUT /config` - Update agent configuration
- `GET /tools` - Get available tools

### MCP Server (Port 8001)

- Tools: `web_search`, `read_file`, `write_file`, `list_directory`, `calculate`, `get_system_info`, `transcribe_audio`

## 🔧 Usage Examples

### Send a Message via API

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Can you help me search for information about AI?"}'
```

### Use Ray Serve Tools Directly

```bash
# Web search
curl -X POST http://localhost:8003/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence"}'

# Calculate
curl -X POST http://localhost:8003/tools/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression": "15 * 23"}'

# System info
curl -X POST http://localhost:8003/tools/get_system_info \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Check System Health

```bash
# Agent API health
curl http://localhost:8002/health

# Ray Serve tools health
curl http://localhost:8003/tools/health
```

### Get Available Tools

```bash
curl http://localhost:8002/tools
```

### Test the System

```bash
python main.py test
```

## 🏛️ Project Structure

```
digital-clone/
├── agent/                 # LangGraph agent system
│   ├── __init__.py
│   ├── models.py         # Data models and types
│   ├── mcp_client.py     # MCP server client
│   ├── graph.py          # LangGraph workflow
│   ├── api.py            # Flask REST API
│   └── run.py            # Agent startup script
├── mcp_server/           # FastMCP server (thin proxy)
│   ├── __init__.py
│   ├── server.py         # MCP server implementation
│   └── run.py            # MCP startup script
├── tools_server/         # Ray Serve tools server
│   ├── __init__.py
│   ├── tools.py          # Ray Serve tools implementation
│   └── run.py            # Ray Serve startup script
├── ui/                   # Web interface
│   └── index.html        # Chat UI
├── main.py               # Main entry point
├── pyproject.toml        # Dependencies
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

The application automatically loads environment variables from a `.env` file in the project root. All modules (agent, MCP server, main) will load these variables on startup.

```bash
# Agent Configuration
AGENT_MODEL=llama3:8b
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=1000
AGENT_SYSTEM_PROMPT="You are a helpful AI assistant."
AGENT_ENABLE_TOOLS=true

# MCP Server
MCP_SERVER_URL=http://localhost:8001

# OpenAI (for Whisper transcription)
OPENAI_API_KEY=your_api_key_here
```

### Agent Configuration via API

```bash
# Update agent configuration
curl -X PUT http://localhost:8002/config \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8, "system_prompt": "You are a coding assistant."}'
```

## 🧪 Testing

### Manual Testing

1. Start the system: `python main.py start`
2. Open the UI: `ui/index.html`
3. Send test messages
4. Check tool usage in responses

### Automated Testing

```bash
# Run system test
python main.py test
```

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not running**
   ```bash
   ollama serve
   ```

2. **Model not found**
   ```bash
   ollama pull llama3:8b
   ```

3. **Port conflicts**
   - Check if ports 8001, 8002 are available
   - Kill existing processes: `lsof -ti:8001 | xargs kill -9`

4. **Import errors**
   ```bash
   pip install -e .
   ```

### Debug Mode

Start components with debug logging:

```bash
# Agent with debug
python agent/run.py

# MCP with debug
python mcp_server/run.py
```

## 🚀 Development

### Adding New Tools

1. Add tool to `mcp_server/server.py`
2. Update tool descriptions in `agent/api.py`
3. Test with `python main.py test`

### Customizing the Agent

1. Modify `agent/graph.py` for workflow changes
2. Update prompts in the agent nodes
3. Adjust configuration in `agent/models.py`

### UI Customization

1. Edit `ui/index.html` for UI changes
2. Add new features to the JavaScript class
3. Integrate with additional APIs

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Test with the provided examples
4. Open an issue with detailed information

---

**Happy coding with your Digital Clone! 🤖✨**
