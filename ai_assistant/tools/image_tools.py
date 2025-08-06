import os
import time
import base64
import platform
import subprocess
import requests
from PIL import Image

# Tool definitions
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

# Tool implementations
def generate_image(prompt, negative_prompt="", steps=20, width=512, height=512):
    """Generate an image using Stable Diffusion API running locally on port 7860"""
    GENERATED_DIR = "./images/generated_images"
    try:
        # Prepare the API request payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "width": width,
            "height": height,
            "sampler_name": "DPM++ 2M Karras",  # Use a good default sampler
            "cfg_scale": 7.0,                    # Default creativity scale
            "seed": -1,                          # Random seed
            "batch_size": 1
        }

        # Call the Stable Diffusion API
        response = requests.post(
            "http://127.0.0.1:7860/sdapi/v1/txt2img",
            json=payload
        )

        if response.status_code != 200:
            return {"error": f"API call failed with status code: {response.status_code}"}

        response_data = response.json()

        # Prepare file paths
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        images = []

        # Process and save all generated images
        for i, img_data in enumerate(response_data.get("images", [])):
            # The API returns base64 encoded images
            img_data = img_data.split(",", 1)[0] if "," in img_data else img_data

            # Decode and save the image
            img_bytes = base64.b64decode(img_data)
            img_path = os.path.join(GENERATED_DIR, f"generation-{timestamp}-{i}.png")

            with open(img_path, "wb") as img_file:
                img_file.write(img_bytes)

            # Add to list of generated images
            # Use relative path for better display in the UI
            relative_path = os.path.relpath(img_path, start=os.path.dirname("./images"))
            images.append(relative_path)

        return {
            "status": "success",
            "prompt": prompt,
            "images": images,
            "message": f"Successfully generated {len(images)} image(s)"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate image: {str(e)}"
        }

def open_saved_image(filename):
    """Open a saved image using the default image viewer"""
    GENERATED_DIR = "./images/generated_images"
    DOWNLOADED_DIR = "./images/downloaded_images"
    IMAGE_DIR = "./images"
    try:
        # Try to find the image in both directories
        if os.path.exists(os.path.join(GENERATED_DIR, filename)):
            filepath = os.path.join(GENERATED_DIR, filename)
        elif os.path.exists(os.path.join(DOWNLOADED_DIR, filename)):
            filepath = os.path.join(DOWNLOADED_DIR, filename)
        else:
            # Handle special case where user provides just the base name
            for root, _, files in os.walk(IMAGE_DIR):
                for file in files:
                    if filename in file:
                        filepath = os.path.join(root, file)
                        break
                else:
                    continue
                break
            else:
                return {"error": f"Image {filename} not found"}

        # Open the image with the default image viewer
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', filepath])
        else:  # Linux
            subprocess.run(['xdg-open', filepath])

        return {
            "status": "success",
            "message": f"Opened image: {filepath}",
            "path": filepath
        }

    except Exception as e:
        return {"error": f"Failed to open image: {str(e)}"}

# Export tools
tools = [TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL]
tool_functions = {
    "generate_image": generate_image,
    "open_saved_image": open_saved_image,
}
