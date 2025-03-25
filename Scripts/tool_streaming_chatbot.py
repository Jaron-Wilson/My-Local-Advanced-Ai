from openai import OpenAI
import time
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler
import os
import json
import requests
from bs4 import BeautifulSoup
import re
from PIL import Image
from pathlib import Path
import platform
import subprocess
import shutil
import urllib.request
import base64  # For base64 encoding/decoding of images
import glob  # For pattern matching in file listing
from dotenv import load_dotenv
load_dotenv()

# Create directories for images
IMAGE_DIR = "./images"
GENERATED_DIR = os.path.join(IMAGE_DIR, "generated_images")
DOWNLOADED_DIR = os.path.join(IMAGE_DIR, "downloaded_images")

os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(DOWNLOADED_DIR, exist_ok=True)

# Initialize OpenAI client with LM Studio endpoint
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
MODEL = "qwen2.5-7b-instruct-1m"  # Default model

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

# Text-to-Image generation tool
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

# Tool for opening a saved image
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

# Tool for opening any file with the system's default application
OPEN_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "open_file",
        "description": "Open any file with the system's default application",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Full path to the file to open"}
            },
            "required": ["filepath"]
        }
    }
}

# Tool for listing files in a directory
LIST_FILES_TOOL = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files in a directory",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list files from"},
                "pattern": {"type": "string", "description": "Optional file pattern to filter by (e.g. *.txt)", "default": "*"}
            },
            "required": ["path"]
        }
    }
}

# Weather Tools
GET_WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            "required": ["location"]
        }
    }
}

GET_WEATHER_FORECAST_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            "required": ["location"]
        }
    }
}

# Tool for downloading files from a URL
DOWNLOAD_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "download_file",
        "description": "Download a file directly from a URL to the local computer",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the file to download (e.g., https://example.com/file.pdf)"},
                "save_path": {"type": "string", "description": "Local path where the file should be saved (e.g., C:/Downloads/file.pdf)"}
            },
            "required": ["url", "save_path"]
        }
    }
}

# Tool for moving files
MOVE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "move_file",
        "description": "Move a file from one location to another",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path"},
                "destination": {"type": "string", "description": "Destination file path or directory"}
            },
            "required": ["source", "destination"]
        }
    }
}

# Tool for copying files
COPY_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "copy_file",
        "description": "Copy a file from one location to another",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path"},
                "destination": {"type": "string", "description": "Destination file path or directory"}
            },
            "required": ["source", "destination"]
        }
    }
}

# Tool for deleting files
DELETE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "delete_file",
        "description": "Delete a file from the file system",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to delete"}
            },
            "required": ["path"]
        }
    }
}

# Tool for renaming files
RENAME_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "rename_file",
        "description": "Rename a file to a new name",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to rename"},
                "new_name": {"type": "string", "description": "New name for the file, including extension"}
            },
            "required": ["path", "new_name"]
        }
    }
}

# Tool for analyzing file content
ANALYZE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_file",
        "description": "Analyze the content of a specified file and return its content",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to analyze"}
            },
            "required": ["file_path"]
        }
    }
}

# Tool implementations
def get_current_time():
    return {"time": time.strftime("%H:%M:%S")}

def get_current_date():
    return {"date": time.strftime("%Y-%m-%d")}

def google_search(query):
    try:
        # Use a shorter pause time and limit results to 3 to avoid timeouts
        results = list(search(query, num=3, pause=2.0, stop=3))
        return {"results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}

def handle_image_files(query, override=False):
    """Helper function to manage image files"""
    if not os.path.exists(DOWNLOADED_DIR):
        os.makedirs(DOWNLOADED_DIR)
    
    if override and os.path.exists(DOWNLOADED_DIR):
        # Remove existing images if override is True
        for file in os.listdir(DOWNLOADED_DIR):
            os.remove(os.path.join(DOWNLOADED_DIR, file))
    
    base_path = os.path.join(DOWNLOADED_DIR, query.replace(" ", "_"))
    suffix = 1
    while os.path.exists(f"{base_path}_{suffix}"):
        suffix += 1
    
    return f"{base_path}_{suffix}"

def google_image_search(query):
    # First check if there are existing images
    if os.path.exists(DOWNLOADED_DIR) and os.listdir(DOWNLOADED_DIR):
        return {"status": "confirm_override", "query": query}
    
    return perform_image_search(query)

def perform_image_search(query, override=False):
    save_dir = handle_image_files(query, override)
    
    crawler = GoogleImageCrawler(storage={"root_dir": os.path.dirname(save_dir)})
    crawler.crawl(keyword=query, max_num=3)
    
    # Rename downloaded files to our desired format
    files = os.listdir(os.path.dirname(save_dir))
    if files:
        for i, file in enumerate(files, 1):
            old_path = os.path.join(os.path.dirname(save_dir), file)
            new_path = f"{save_dir}_{i}{os.path.splitext(file)[1]}"
            os.rename(old_path, new_path)
        return {"image_paths": [f"{save_dir}_{1}"]}
    return {"error": "No images found"}

def clean_text(text):
    """Clean extracted text by removing extra whitespace and unwanted characters"""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
    return text.strip()

def read_webpage(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract main content (adjust selectors based on common website structures)
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if (main_content):
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3'])
            content = '\n'.join(p.get_text() for p in paragraphs)
        else:
            content = soup.get_text()
        
        cleaned_content = clean_text(content)
        return {"content": cleaned_content[:2000]}  # Limit content length
    except Exception as e:
        return {"error": f"Failed to read webpage: {str(e)}"}

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

def list_available_images():
    """List all available images in both the generated and downloaded directories"""
    images = []
    
    # Check generated images
    if os.path.exists(GENERATED_DIR):
        for file in os.listdir(GENERATED_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                # Use relative path for better display in the UI
                relative_path = os.path.join("generated_images", file)
                images.append(relative_path)
    
    # Check downloaded images
    if os.path.exists(DOWNLOADED_DIR):
        for file in os.listdir(DOWNLOADED_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                # Use relative path for better display in the UI
                relative_path = os.path.join("downloaded_images", file)
                images.append(relative_path)
    
    return {"images": images}

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

def open_file(filepath):
    """Open a file with the system's default application"""
    try:
        # Verify the file exists
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        # Open the file with the default application based on the OS
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', filepath])
        else:  # Linux
            subprocess.run(['xdg-open', filepath])
        
        return {
            "status": "success", 
            "message": f"Opened file: {filepath}"
        }
    
    except Exception as e:
        return {"error": f"Failed to open file: {str(e)}"}

def list_files(path, pattern="*"):
    """List files in a directory with optional pattern matching"""
    try:
        # Validate the path exists
        if not os.path.exists(path):
            return {"error": f"Path not found: {path}"}
        
        # Check if it's a directory
        if not os.path.isdir(path):
            return {"error": f"Not a directory: {path}"}
        
        # List files with the given pattern
        files = []
        directories = []
        
        # Use glob for pattern matching
        for item in glob.glob(os.path.join(path, pattern)):
            if os.path.isfile(item):
                # Get file details
                file_stats = os.stat(item)
                size_bytes = file_stats.st_size
                modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stats.st_mtime))
                
                # Format size to be more readable
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes/1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes/(1024*1024):.1f} MB"
                else:
                    size_str = f"{size_bytes/(1024*1024*1024):.1f} GB"
                
                files.append({
                    "name": os.path.basename(item),
                    "path": item,
                    "size": size_str,
                    "modified": modified_time
                })
            elif os.path.isdir(item):
                directories.append({
                    "name": os.path.basename(item),
                    "path": item,
                    "type": "directory"
                })
        
        return {
            "path": path,
            "pattern": pattern,
            "directories": directories,
            "files": files,
            "total_dirs": len(directories),
            "total_files": len(files)
        }
    except Exception as e:
        return {"error": f"Error listing files: {str(e)}"}

def get_weather(location):
    """Fetch current weather for a given location using WeatherAPI"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {"error": "API key for WeatherAPI is missing. Please check your .env file."}

        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": f"Failed to fetch weather data. Status code: {response.status_code}"}

        data = response.json()
        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"]
        }
    except Exception as e:
        return {"error": f"An error occurred while fetching weather data: {str(e)}"}

def get_weather_forecast(location):
    """Fetch weather forecast for a given location using WeatherAPI"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {"error": "API key for WeatherAPI is missing. Please check your .env file."}

        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": f"Failed to fetch weather forecast. Status code: {response.status_code}"}

        data = response.json()
        forecast = []
        for day in data["forecast"]["forecastday"]:
            forecast.append({
                "date": day["date"],
                "max_temp_c": day["day"]["maxtemp_c"],
                "min_temp_c": day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"]
            })

        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "forecast": forecast
        }
    except Exception as e:
        return {"error": f"An error occurred while fetching weather forecast: {str(e)}"}

def download_file(url, save_path):
    """Download a file from a URL to the specified local path"""
    try:
        # Make the HTTP request to download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Write the file to the specified path
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return {
            "status": "success",
            "message": f"File downloaded successfully to {save_path}",
            "path": save_path
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to download file: {str(e)}"
        }

def move_file(source, destination):
    try:
        shutil.move(source, destination)
        return {"status": "success", "message": f"Moved file from {source} to {destination}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move file: {str(e)}"}

def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
        return {"status": "success", "message": f"Copied file from {source} to {destination}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy file: {str(e)}"}

def delete_file(path):
    try:
        os.remove(path)
        return {"status": "success", "message": f"Deleted file: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete file: {str(e)}"}

def rename_file(path, new_name):
    try:
        directory = os.path.dirname(path)
        new_path = os.path.join(directory, new_name)
        os.rename(path, new_path)
        return {"status": "success", "message": f"Renamed file to {new_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rename file: {str(e)}"}

def analyze_file(file_path):
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": f"Failed to analyze file: {str(e)}"}

def process_stream(stream, add_assistant_label=True):
    """Handle streaming responses from the API"""
    collected_text = ""
    tool_calls = []
    first_chunk = True
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Handle regular text output
        if delta.content:
            if first_chunk:
                print()
                if add_assistant_label:
                    print("Assistant:", end=" ", flush=True)
                first_chunk = False
            print(delta.content, end="", flush=True)
            collected_text += delta.content
            
        # Handle tool calls
        elif delta.tool_calls:
            for tc in delta.tool_calls:
                if len(tool_calls) <= tc.index:
                    tool_calls.append({
                        "id": "", 
                        "type": "function",
                        "function": {"name": "", "arguments": ""}
                    })
                    
                tool_calls[tc.index] = {
                    "id": (tool_calls[tc.index]["id"] + (tc.id or "")),
                    "type": "function",
                    "function": {
                        "name": (tool_calls[tc.index]["function"]["name"] + (tc.function.name or "")),
                        "arguments": (tool_calls[tc.index]["function"]["arguments"] + (tc.function.arguments or ""))
                    }
                }
                
    return collected_text, tool_calls

def chat_loop():
    messages = []
    pending_image_query = None
    
    print("Assistant: Hi! I am an AI agent empowered with various tools including web browsing. (Type 'quit' to exit)")
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == "quit":
            break
            
        # Handle pending image override confirmation
        if pending_image_query:
            if user_input.lower() in ['yes', 'y']:
                result = perform_image_search(pending_image_query["query"], override=True)
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": pending_image_query["tool_call_id"]
                })
            elif user_input.lower() in ['no', 'n']:
                result = perform_image_search(pending_image_query["query"], override=False)
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": pending_image_query["tool_call_id"]
                })
            pending_image_query = None
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        # Get initial response
        response_text, tool_calls = process_stream(
            client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL,
                       GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL, 
                       TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, OPEN_FILE_TOOL, LIST_FILES_TOOL, DOWNLOAD_FILE_TOOL,
                       MOVE_FILE_TOOL, COPY_FILE_TOOL, DELETE_FILE_TOOL, RENAME_FILE_TOOL, ANALYZE_FILE_TOOL],
                stream=True,
                temperature=0.2
            )
        )
        
        if not tool_calls:
            print()
            
        text_in_first_response = len(response_text) > 0
        if text_in_first_response:
            messages.append({"role": "assistant", "content": response_text})
            
        # Handle tool calls if any
        if tool_calls:
            tool_name = tool_calls[0]["function"]["name"]
            print()
            if not text_in_first_response:
                print("Assistant:", end=" ", flush=True)
            print(f"**Calling Tool: {tool_name}**")
            
            messages.append({"role": "assistant", "tool_calls": tool_calls})
            
            # Execute tool calls
            for tool_call in tool_calls:
                try:
                    query_args = json.loads(tool_call["function"]["arguments"])
                    query = query_args.get("query", "")
                except json.JSONDecodeError:
                    print("Error: Invalid JSON arguments.")
                    continue
                    
                if tool_call["function"]["name"] == "get_current_time":
                    result = get_current_time()
                elif tool_call["function"]["name"] == "get_current_date":
                    result = get_current_date()
                elif tool_call["function"]["name"] == "google_search":
                    result = google_search(query)
                elif tool_call["function"]["name"] == "google_image_search":
                    result = google_image_search(query)
                    if result.get("status") == "confirm_override":
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)")
                        pending_image_query = {
                            "query": result["query"],
                            "tool_call_id": tool_call["id"]
                        }
                        continue
                elif tool_call["function"]["name"] == "read_webpage":
                    result = read_webpage(query_args["url"])
                elif tool_call["function"]["name"] == "generate_image":
                    result = generate_image(
                        prompt=query_args["prompt"],
                        negative_prompt=query_args.get("negative_prompt", ""),
                        steps=query_args.get("steps", 20),
                        width=query_args.get("width", 512),
                        height=query_args.get("height", 512)
                    )
                elif tool_call["function"]["name"] == "open_saved_image":
                    result = open_saved_image(query_args["filename"])
                elif tool_call["function"]["name"] == "open_file":
                    result = open_file(query_args["filepath"])
                elif tool_call["function"]["name"] == "list_files":
                    result = list_files(
                        path=query_args["path"],
                        pattern=query_args.get("pattern", "*")
                    )
                elif tool_call["function"]["name"] == "get_weather":
                    result = get_weather(query_args["location"])
                elif tool_call["function"]["name"] == "get_weather_forecast":
                    result = get_weather_forecast(query_args["location"])
                elif tool_call["function"]["name"] == "download_file":
                    result = download_file(
                        url=query_args["url"],
                        save_path=query_args["save_path"]
                    )
                elif tool_call["function"]["name"] == "move_file":
                    result = move_file(
                        source=query_args["source"],
                        destination=query_args["destination"]
                    )
                elif tool_call["function"]["name"] == "copy_file":
                    result = copy_file(
                        source=query_args["source"],
                        destination=query_args["destination"]
                    )
                elif tool_call["function"]["name"] == "delete_file":
                    result = delete_file(query_args["path"])
                elif tool_call["function"]["name"] == "rename_file":
                    result = rename_file(
                        path=query_args["path"],
                        new_name=query_args["new_name"]
                    )
                elif tool_call["function"]["name"] == "analyze_file":
                    result = analyze_file(query_args["file_path"])
                
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": tool_call["id"]
                })
                
            # If we didn't have a pending image query, get final response after tool execution
            if not pending_image_query:
                final_response, _ = process_stream(
                    client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        stream=True
                    ),
                    add_assistant_label=False
                )
                
                if final_response:
                    print()
                    messages.append({"role": "assistant", "content": final_response})

if __name__ == "__main__":
    chat_loop()
