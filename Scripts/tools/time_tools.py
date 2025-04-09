"""
Time and date related tools
"""

# Tool definitions
TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Get the current time, only if asked",
        "parameters": {"type": "object", "properties": {}}
    }
}

DATE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_date",
        "description": "Get the current date, only if asked",
        "parameters": {"type": "object", "properties": {}}
    }
}
