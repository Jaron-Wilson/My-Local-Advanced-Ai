# AI Assistant with Tool Integration

A modular AI assistant that can interact with various tools through function calling capabilities, built to work with LM Studio.

## Overview

This project implements a conversational AI assistant with modular components and tool integration capabilities. The assistant can:

- Interact with users in a chat-like interface
- Execute various tools/functions to perform real-world tasks
- Search for and manipulate files
- Search the web for information
- Process and generate images
- Provide system information

## Project Structure

```
ai_assistant/               # Main package
├── __init__.py            
├── config.py              # Configuration loading
├── core/                  # Core components
│   ├── __init__.py
│   ├── chat_engine.py     # Main chat loop implementation
│   └── model_manager.py   # Model management
├── tools/                 # Tool implementations
│   ├── __init__.py
│   ├── file_tools.py      # File operations tools
│   ├── image_tools.py     # Image search and manipulation
│   ├── sdk_tools.py       # LM Studio SDK integration
│   ├── system_tools.py    # System information tools
│   ├── tool_processor.py  # Tool execution processor
│   ├── tool_registry.py   # Tool registration and management
│   └── web_tools.py       # Web search and content tools
└── utils/                 # Utility functions
    ├── __init__.py
    ├── logging_utils.py   # Logging configuration
    └── sdk_utils.py       # SDK helper functions
```

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure LM Studio is running (with API server enabled)

## Usage

Run the main script to start the assistant:

```bash
python Scripts/tool_streaming_chatbot.py
```

### Command Line Options

- `--model`, `-m`: Specify a model to use
- `--tools-file`, `-t`: Path to YAML file with additional tool definitions
- `--single-tool-mode`, `-s`: Run in single tool call mode (disables multiple tool calls)

## Available Tools

### System Tools
- Get system information
- Get current time
- Check internet connection

### File Tools
- Search files
- Read files
- Write files 
- List directories
- Get file information

### Image Tools
- Search for images
- Download images
- List local images

### Web Tools
- Search the web
- Get weather information
- Fetch webpage content

### SDK Tools
- List available models
- Select specialized models
- Load/unload models

## Extending with New Tools

You can extend the assistant with new tools by:

1. Creating a new tool provider class
2. Implementing the required methods:
   - `get_api_tools()`: Schema for OpenAI API compatibility
   - `get_sdk_tools()`: Functions for LM Studio SDK
   - `execute_tool()`: Main implementation
3. Registering the tool provider in the `ToolRegistry`

## Configuration

Configuration is loaded from environment variables and defaults in `config.py`.

## License

[MIT License](LICENSE)