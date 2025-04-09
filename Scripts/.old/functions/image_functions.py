"""
Image generation and manipulation function implementations
"""
import os
import time
import platform
import subprocess
import base64
import requests
from ..tools.config import GENERATED_DIR, DOWNLOADED_DIR, IMAGE_DIR

def generate_image(prompt, negative_prompt="", steps=20, width=512, height=512):
    """Generate an image using Stable Diffusion API running locally on port 7860"""
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
            relative_path = os.path.relpath(img_path, start=os.path.dirname(IMAGE_DIR))
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

def what_is_this_image(image_path):
    """Analyze an image using an LLM with vision capabilities"""
    try:
        from openai import OpenAI
        
        # Initialize client with the local endpoint
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        completion = client.chat.completions.create(
            model="gemma-3-4b-it",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that analyzes images.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
            stream=False
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return {"error": f"Failed to analyze image: {str(e)}"}
