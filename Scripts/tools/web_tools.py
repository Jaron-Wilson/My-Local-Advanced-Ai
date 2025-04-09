"""
Web content extraction tools
"""

# Webpage reading tool definition
WEBPAGE_READ_TOOL = {
    "type": "function",
    "function": {
        "name": "read_webpage",
        "description": "Read and summarize the content of a webpage",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the webpage to read"}
            },
            "required": ["url"]
        }
    }
}
