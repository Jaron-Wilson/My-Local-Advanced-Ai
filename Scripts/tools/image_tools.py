"""
Image generation and manipulation tools
"""

# Text-to-Image generation tool definition
TEXT_TO_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_image",
        "description": "Generate an image from a text description using Stable Diffusion",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Detailed description of the image to generate"},
                "negative_prompt": {"type": "string", "description": "Things to avoid in the generated image"},
                "steps": {"type": "integer", "description": "Number of sampling steps (higher = more detail but slower)"},
                "width": {"type": "integer", "description": "Width of the generated image (default is 512)"},
                "height": {"type": "integer", "description": "Height of the generated image (default is 512)"}
            },
            "required": ["prompt"]
        }
    }
}

# Image opening tool definition
OPEN_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "open_saved_image",
        "description": "Open a previously saved image",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The filename of the image to open"}
            },
            "required": ["filename"]
        }
    }
}

# Image analysis tool definition
WHAT_IS_THIS_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "what_is_this_image",
        "description": "Analyze an image and provide a description of its content",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to the image file to analyze"},
                "local": {
                    "type": "boolean",
                    "description": "Indicates if the image is local or api use"
                }
            },
            "required": ["image_path", "local"]  # List of required parameters
        }
    }
}
