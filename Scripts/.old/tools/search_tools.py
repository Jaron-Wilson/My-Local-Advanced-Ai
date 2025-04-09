"""
Web search related tools
"""

# Google search tool definition
GOOGLE_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "google_search",
        "description": "Perform a Google search and return the top result.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to look up."}
            },
            "required": ["query"]
        }
    }
}

# Google image search tool definition
GOOGLE_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "google_image_search",
        "description": "Search for an image on Google and download it.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The image search term."}
            },
            "required": ["query"]
        }
    }
}
