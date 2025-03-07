# AI Assistant: Complete Documentation

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Web Interface](#web-interface)
- [API Reference](#api-reference)
- [Tools & Capabilities](#tools--capabilities)
- [Model Management](#model-management)
- [System Architecture](#system-architecture)
- [Installation Guide](#installation-guide)
- [Security Considerations](#security-considerations)
- [Developer Notes](#developer-notes)

## Overview

This AI Assistant integrates powerful language models with a comprehensive suite of tools to help accomplish real-world tasks through natural language. Unlike typical chatbots, this assistant can access and manipulate your local environment, search the web, generate images, manage files, and much more.

The system provides:
- **Conversational AI**: Natural language interaction with an AI model
- **Tool Integration**: Seamless use of various tools through conversation
- **Web Interface**: Clean, modern web UI for human interaction
- **REST API**: Comprehensive API for integration with other applications
- **File System Access**: Safe, controlled access to your local files
- **Markdown Support**: Rich text formatting in responses
- **Model Management**: Dynamic loading and unloading of AI models using the LM Studio SDK
- **Multiple Tool Execution**: Execute multiple tools in a single request using native SDK capabilities

## Features

### Information Retrieval
- **Internet Search**: Search the web for information
- **Web Page Reading**: Extract and summarize content from web pages
- **Background Checks**: Gather publicly available information about individuals
- **YouTube Transcription**: Extract and summarize YouTube video content

### Multimedia
- **Image Generation**: Create images from text descriptions using Stable Diffusion
- **Google Image Search**: Find and download relevant images
- **Image Management**: List, view, and organize images
- **Voice Input/Output**: Convert speech to text and text to speech

### System Utilities
- **Date and Time**: Get current date/time information
- **Weather Data**: Retrieve current weather and forecasts
- **PDF Analysis**: Extract and analyze text from PDF files
- **File Management**: List, move, copy, download, and delete files

### Model Management
- **Model Switching**: Select specialized models for different tasks
- **Dynamic Loading**: Load models directly via LM Studio SDK
- **Resource Management**: Unload models when not needed
- **Model Information**: List available and currently loaded models
- **Native SDK Integration**: Direct model interaction using LM Studio's Python SDK

## Web Interface

The web interface is available at `http://localhost:8000` and provides:

- **Chat Interface**: Send messages and view AI responses
- **Tool Access**: Buttons for quick access to common tools
- **Image Display**: View generated and downloaded images
- **Voice Controls**: Speak to your assistant and hear responses

### Example Use Cases

#### Research Assistant
```
You: I need to research quantum computing for a paper. Can you help?
Assistant: I'd be happy to help with your quantum computing research. Let me search for some information...

*Assistant provides search results, summaries from academic sources, and offers to save key information to a file*
```

#### Creative Partner
```
You: I need a logo for my bakery called "Sweet Mornings"
Assistant: I'll help create a logo concept for "Sweet Mornings" bakery.

*Assistant generates images of logo concepts, which you can refine through conversation*
```

#### Productivity Helper
```
You: I need to organize my Downloads folder
Assistant: I can help with that. Let me check what's in your Downloads folder.

*Assistant lists files, suggests categories, and helps move them to appropriate locations*
```

## API Reference

### Chat and Conversation

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/chat` | POST | Single-turn chat | `content`: Text message<br>`markdown`: Boolean to enable markdown |
| `/conversation` | POST | Multi-turn conversation | Array of message objects with `role` and `content` fields |

### Tools

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/tool` | POST | Generic tool caller | `tool`: Tool name<br>`args`: Tool arguments |
| `/weather/current` | POST | Current weather | `location`: City name or coordinates |
| `/weather/forecast` | POST | Weather forecast | `location`: City name or coordinates |
| `/generate` | POST | Generate image | `prompt`: Text description<br>`negative_prompt`: Things to avoid<br>`steps`: Processing steps<br>`width`: Image width<br>`height`: Image height |
| `/speak` | POST | Text to speech | `text`: Text to convert to speech |
| `/listen` | GET | Voice input | None |

### Files and Images

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/images` | GET | List available images | None |
| `/image/{path}` | GET | Serve image file | `path`: Path parameter |
| `/files/list` | POST | List files | `path`: Directory path<br>`pattern`: Filter pattern |
| `/files/move` | POST | Move file | `source`: Source path<br>`destination`: Destination path |
| `/files/copy` | POST | Copy file | `source`: Source path<br>`destination`: Destination path |
| `/files/delete` | POST | Delete file | `path`: File path |
| `/files/download` | POST | Download file | `url`: Source URL<br>`save_path`: Path to save file |

### Model Management

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/models` | GET | List all available models | None |
| `/models/loaded` | GET | List currently loaded models | None |
| `/models/select` | POST | Select a specialized model | `task_type`: The type of task ("summarization", "analysis", "creative", "coding", "default") |
| `/models/load` | POST | Load a model into memory | `model_id`: The model identifier to load |
| `/models/unload` | POST | Unload a model from memory | `model_id`: The model identifier to unload |

### Example API Usage

```bash
# Generate an image
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "sunset over mountains with a lake"}'

# Get weather information
curl -X POST http://localhost:8000/weather/current \
  -H "Content-Type: application/json" \
  -d '{"location": "New York"}'

# List directory contents
curl -X POST http://localhost:8000/files/list \
  -H "Content-Type: application/json" \
  -d '{"path": "C:/Users/username/Downloads"}'

# List available models
curl -X GET http://localhost:8000/models

# Check which models are currently loaded
curl -X GET http://localhost:8000/models/loaded

# Select a model for a specific task
curl -X POST http://localhost:8000/models/select \
  -H "Content-Type: application/json" \
  -d '{"task_type": "creative"}'

# Load a specific model
curl -X POST http://localhost:8000/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "gemma-2-2b-it"}'

# Unload a model to free up memory
curl -X POST http://localhost:8000/models/unload \
  -H "Content-Type: application/json" \
  -d '{"model_id": "gemma-2-2b-it"}'
```

## Tools & Capabilities

The AI can use the following tools through natural language requests:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_current_time` | Get the current time | "What time is it now?" |
| `get_current_date` | Get the current date | "What's today's date?" |
| `google_search` | Search the web | "Search for latest AI developments" |
| `google_image_search` | Find images | "Find me images of mountain landscapes" |
| `read_webpage` | Extract webpage content | "Summarize the content from example.com" |
| `background_check` | Get information on a person | "What can you tell me about John Smith?" |
| `listen_voice` | Convert speech to text | "Listen to my voice input" |
| `speak_text` | Convert text to speech | "Read this text aloud" |
| `analyze_pdf` | Extract PDF content | "Analyze the resume.pdf file" |
| `summarize_youtube` | Get video transcript | "Summarize the YouTube video dQw4w9WgXcQ" |
| `get_weather_current` | Current weather | "What's the weather in London?" |
| `get_weather_forecast` | Weather forecast | "Forecast for Tokyo this week" |
| `generate_image` | Create images | "Generate an image of a sunset over mountains" |
| `open_saved_image` | View saved images | "Show me saved images" |
| `list_files` | List directory contents | "Show files in Downloads folder" |
| `move_file` | Move files | "Move budget.xlsx from Downloads to Documents" |
| `copy_file` | Copy files | "Copy report.docx to my backup folder" |
| `delete_file` | Delete files | "Delete temp.txt" |
| `download_file` | Download from URL | "Download image from https://example.com/image.jpg" |
| `list_available_models` | List all models | "What AI models are available?" |
| `select_model` | Select model for task | "Use the creative model for my next request" |
| `load_model` | Load model into memory | "Load the Gemma model" |
| `unload_model` | Unload model from memory | "Unload the Llama model to free up resources" |

## Model Management

The assistant can dynamically manage different AI models for specialized tasks using the LM Studio SDK:

### Available Task Types
- **Summarization**: Optimized for summarizing documents and web content
- **Analysis**: Best for analytical reasoning and complex data analysis
- **Creative**: Specialized for creative writing and content generation
- **Coding**: Tailored for programming and technical documentation
- **Default**: General-purpose conversation and task handling

### Model Management Features
- **Direct SDK Integration**: Uses the LM Studio SDK to interact with models
- **Multiple Tool Calling**: Execute multiple tools in a single request
- **Automatic Fallback**: Falls back to OpenAI-compatible API if SDK methods fail
- **Runtime Model Loading**: Load and unload models without restarting
- **Real-time Model Status**: Check which models are currently loaded in memory
- **Temporary Model Instances**: Create and use temporary model instances for one-time tasks
- **Resource Management**: Automatically unload temporary models when no longer needed

### Model Loading Options
- **Main Model Loading**: Load a model as the primary conversation model
- **Temporary Instances**: Create temporary model instances for specialized tasks
- **Multiple Instances**: Run multiple instances of the same model simultaneously
- **Automatic Detection**: Detect whether a task requires a temporary instance

### Model Selection Workflow
1. Check available models: `list_available_models`
2. Check currently loaded models: `check_loaded_models`
3. Select appropriate model for task: `select_model`
4. Choose loading approach:
   - For persistent models: `load_model(model_id)`
   - For temporary models: `load_model(model_id, temp_instance=True, instance_name="task-name")`
5. Use the model for your task
6. For temporary models: System automatically unloads when task completes
7. For persistent models: Explicitly unload when needed `unload_model(model_id)`

### Example Usage

```
You: What models do you have available?
Assistant: I'll check the available models for you.

*Assistant lists the currently available models and their specializations*

You: I want to write a short story about a robot that falls in love with a refrigerator
Assistant: That sounds like a creative writing task. Let me select the best model for creative tasks.

*Assistant selects and loads the creative model*

You: Now for a quick analysis of this data, but don't change the main model
Assistant: I'll create a temporary instance of an analytical model for this task.

*Assistant creates temporary model instance, performs analysis, then unloads it*

You: Now let's continue with our story
Assistant: *Continues using the creative model that remains loaded*
```

## System Architecture

### Component Diagram

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  LM Studio SDK  │◄────►│   FastAPI       │◄────►│   Web Browser   │
│  Integration    │      │   Backend       │      │   Interface     │
│                 │      │                 │      │                 │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
        ▲                         │
        │                 ┌───────┴───────┐
        │                 │               │
        └─────────────────┤  Tool Suite   │
                          │  & Utilities  │
                          │               │
                          └───────────────┘
```

### System Components

1. **LM Studio SDK**: Direct programmatic interaction with LM Studio
2. **FastAPI Server**: API endpoints and web interface
3. **Tool Functions**: Python modules implementing various capabilities
4. **Web UI**: HTML/JS interface for user interaction

### File Structure

```
/examples/
├── Scripts/
│   ├── tool_streaming_chatbot.py  # Core functionality
│   ├── chatbot_api_webaccess.py   # API server
│   └── __init__.py                # Package marker
├── static/
│   └── index.html                 # Web interface
├── images/
│   ├── generated_images/          # AI-generated images
│   └── downloaded_images/         # Google image search results
├── webui/
│   └── run.bat                    # Stable Diffusion launcher
├── docs/
│   └── chatbot_documentation.md   # This documentation
├── run_api.py                     # API startup script
└── requirements.txt               # Dependencies
```

## Installation Guide

### Prerequisites
- Python 3.8+
- [LM Studio](https://lmstudio.ai/) (with SDK support)
- [LM Studio SDK](https://github.com/lmstudio-ai/py-lmstudio) (`pip install lmstudio`)
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) (for image generation)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
pip install lmstudio  # Make sure to install the LM Studio SDK
```

Note: PyAudio may require manual installation on Windows. Download the appropriate wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install with:
```bash
pip install PyAudio-0.2.11-cp39-cp39-win_amd64.whl
```

### Step 2: Environment Configuration
Create a `.env` file with your API keys:
```
WEATHER_API_KEY=your_weather_api_key
```

### Step 3: Start LM Studio
1. Launch LM Studio
2. Load your preferred model
3. Start the local server (default: http://127.0.0.1:1234)

### Step 4: Start Stable Diffusion WebUI (Optional)
If you want image generation capabilities:
```bash
cd webui
run.bat
```

### Step 5: Launch the Assistant
```bash
python run_api.py
```

### Step 6: Access the Interface
Open http://localhost:8000 in your browser

## Security Considerations

⚠️ **Important**: This system has access to your file system. Use with caution.

- The assistant can access, modify, and delete files on your system
- Consider running in a limited user account for security
- Avoid exposing the API to the public internet without proper authentication
- Be cautious with file deletion operations

## Developer Notes

### Using Native Tool Calling with LM Studio SDK

The system now supports native tool calling using the LM Studio SDK:

```python
def my_typed_tool(param1: str, param2: int) -> dict:
    """Tool function with proper type annotations for SDK compatibility"""
    # Tool implementation here
    return {"result": "success"}

# Using the SDK directly to call tools
import lmstudio as lms

# Get a reference to the loaded model
model = lms.llm("model_id")

# Create a chat context
chat = lms.Chat("You are a helpful assistant")

# Add tool functions to the model and call them
model.act(
    chat,
    [my_typed_tool, another_tool],
    on_message=chat.append,
    on_prediction_fragment=print_fragment
)
```

### Advanced Model Management with the SDK

The system supports both persistent and temporary model instances:

```python
# Initialize the SDK client
client = lms.Client()

# Get or load a persistent model (main conversation model)
main_model = client.llm.model("model-id")  # Gets existing or loads if not loaded

# Create a temporary instance for a specific task
temp_model = client.llm.load_new_instance("model-id", "temp-instance-name")

# Use the temporary model
temp_model.act(chat, tools)

# When done, unload the temporary model
await client.llm.unload("temp-instance-name")
```

The assistant will automatically:
1. Detect when a temporary model instance would be beneficial
2. Create named temporary instances for specialized tasks
3. Unload temporary instances when tasks are complete
4. Maintain the main conversation model for continuity

### Extending with New Tools

1. Add a new function in `tool_streaming_chatbot.py` with type hints for SDK compatibility:
```python
def my_new_tool(parameter1: str, parameter2: int = 0) -> dict:
    """Tool description for SDK docstring"""
    # Implementation here
    return {"result": "success"}
```

2. Create a tool definition for OpenAI-compatible API:
```python
MY_NEW_TOOL = {
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "Description of what the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "parameter1": {"type": "string", "description": "Description of parameter"},
                "parameter2": {"type": "integer", "description": "Description of parameter"}
            },
            "required": ["parameter1"]
        }
    }
}
```

3. Add the function to the SDK tools list in `chat_with_tools` function:
```python
tools = [
    get_current_time,
    get_current_date,
    my_new_tool,  # Add the new tool function here
    # Other tools...
]
```

4. Add the tool definition to the OpenAI API tools list:
```python
tools=[TIME_TOOL, ..., MY_NEW_TOOL]
```

5. Add a handler in the tool_calls section for OpenAI API fallback:
```python
elif tool_call["function"]["name"] == "my_new_tool":
    result = my_new_tool(**query_args)
```

6. Create an API endpoint in `chatbot_api_webaccess.py`:
```python
@app.post("/my_new_tool")
async def api_my_new_tool(params: MyNewToolParams):
    try:
        return my_new_tool(params.parameter1, params.parameter2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Troubleshooting

- **Model not responding**: Check that LM Studio is running and the API server is active
- **SDK errors**: Verify that you have the latest version of the LM Studio SDK installed
- **Multiple tool calling issues**: Check if your model supports multiple tool calling; try using the OpenAI API fallback method
- **Model loading failures**: Ensure you have adequate system memory for the model you're trying to load
- **API endpoint errors**: Check the console logs for detailed error messages
- **File permissions**: Verify the application has appropriate access to the file system
- **Memory usage**: If running multiple model instances, monitor system memory usage
- **Temporary instances**: If temporary instances aren't being unloaded properly, use the CLI command `lm-studio models list` to identify orphaned instances
