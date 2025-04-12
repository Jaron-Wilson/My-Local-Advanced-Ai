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
                "query": {
                    "type": "string", 
                    "description": "The search query to look up."
                },
                "max_results": {
                    "type": "integer",
                    "description": "The maximum number of results to return."
                }
            },
            "required": ["query", "max_results"]
        }
    }
}

# Google image search tool definition
GOOGLE_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "google_image_search",
        "description": "Search for an image on Google and download it. Use this if user wants more than one image (returns 3) else use preform_image_search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", "description": "The image search term."
                }
            },
            "required": ["query"]
        }
    }
}

# Perform google image search and download definition
PERFORM_IMAGE_SEARCH = {
    "type": "function",
    "function": {
        "name": "perform_image_search",
        "description": "Perform a Google image search and download the first result.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "The search query to look up."
                },
                "override": {
                    "type": "boolean",
                    "description": "Whether to override existing results."
                }
            },
            "required": ["query", "override"]
        }
    }
}


