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
│   └── chat_engine.py     # Main chat loop implementation
└── tools/                 # Tool implementations
    ├── __init__.py
    ├── file_tools.py      # File operations tools
    ├── image_tools.py     # Image generation and opening
    ├── system_tools.py    # System information tools
    ├── tool_registry.py   # Tool registration and management
    └── web_tools.py       # Web search and content tools
```

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure LM Studio is running (with the API server enabled).
4. If you want to use the weather tools, get a free API key from [WeatherAPI](https://www.weatherapi.com/) and set it as an environment variable named `WEATHER_API_KEY`. You can do this by creating a `.env` file in the root of the project with the following content:
   ```
   WEATHER_API_KEY=your_api_key
   ```

## Usage

Run the main script to start the assistant:

```bash
python run.py
```

## Available Tools

### System Tools
- Get current time
- Get current date
- Get system information (CPU and memory usage)

### Web Tools
- Google search
- Google image search
- Read webpage content
- Download a file from a URL

### File Tools
- Open a file
- List files in a directory
- Move a file
- Copy a file
- Delete a file
- Rename a file
- Analyze file content

### Image Tools
- Generate an image from a text prompt (using Stable Diffusion)
- Open a saved image

### Weather Tools
- Get current weather for a location
- Get a 3-day weather forecast

## Extending with New Tools

The tool registry automatically discovers and loads tools from the `.py` files in the `ai_assistant/tools` directory. To add a new tool:

1.  **Create or choose a tool file:** You can add your tool to an existing file (e.g., `system_tools.py`) or create a new file (e.g., `my_new_tools.py`).
2.  **Define the tool:** Create a dictionary that describes the tool, following the OpenAI function calling format.
3.  **Implement the tool function:** Write the Python function that will be executed when the tool is called.
4.  **Export the tool:** Add your tool definition and function to the `tools` list and `tool_functions` dictionary in the tool file.

For example, to add a `get_username` tool to `system_tools.py`, you would add the following:

```python
# In ai_assistant/tools/system_tools.py

# ... other imports
import getpass

# ... other tool definitions

GET_USERNAME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_username",
        "description": "Get the current user's username.",
        "parameters": {"type": "object", "properties": {}}
    }
}

# ... other tool functions

def get_username():
    return {"username": getpass.getuser()}

# ... update exports

tools = [TIME_TOOL, DATE_TOOL, SYSTEM_INFO_TOOL, GET_USERNAME_TOOL]
tool_functions = {
    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
    "get_system_info": get_system_info,
    "get_username": get_username,
}
```

## Configuration

Configuration is loaded from environment variables and defaults in `ai_assistant/config.py`. You can create a `.env` file in the project root to override the default settings.

## License

[MIT License](LICENSE)