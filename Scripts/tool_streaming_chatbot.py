from openai import OpenAI
import time
import speech_recognition as sr
from gtts import gTTS
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import calendar
import requests
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler
import os
import json
from bs4 import BeautifulSoup
import re
import base64
import urllib.request
from PIL import Image
import subprocess
import shutil
import urllib.parse
import glob
import platform
from pathlib import Path
import fnmatch  # Add for file pattern matching
import csv
import json as json_lib
from collections import Counter
import chardet
import mimetypes
import sys
import asyncio
import lmstudio as lms  # Import LM Studio SDK

from dotenv import load_dotenv

# Configuration settings
ALLOW_MULTIPLE_TOOL_CALLS = True  # Toggle this to True/False to allow/disallow multiple tool calls
LMSTUDIO_API_BASE = "http://127.0.0.1:1234/v1"
LMSTUDIO_API_KEY = "lm-studio"

# Model settings - make DEFAULT_CONVERSATION_MODEL global
global DEFAULT_CONVERSATION_MODEL, AVAILABLE_SPECIALIZED_MODELS, CURRENT_SPECIALIZED_MODEL, API_MODELS
DEFAULT_CONVERSATION_MODEL = "simple_chat"  # Always use this for conversation
AVAILABLE_SPECIALIZED_MODELS = {
    "expert_chat": "qwen2.5-7b-instruct-1m",
    "simple_chat" : "qwen2.5-0.5b-instruct",
    "image_reconization": "llava-v1.5-7b@q2_k",
    "default": DEFAULT_CONVERSATION_MODEL,
}

# Track available models and currently loaded model
API_MODELS = []
CURRENT_SPECIALIZED_MODEL = "expert_chat"
CURRENTLY_LOADED_MODEL = None  # Track which model is currently loaded

# Update directory constants
IMAGE_DIR = "../images"
GENERATED_DIR = os.path.join(IMAGE_DIR, "generated_images/")
DOWNLOADED_DIR = os.path.join(IMAGE_DIR, "downloaded_images/")
# print(f"Generated images directory: {GENERATED_DIR}")
# print(f"Downloaded images directory: {DOWNLOADED_DIR}")

# Load the .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(base_url=LMSTUDIO_API_BASE, api_key=LMSTUDIO_API_KEY)
MODEL = DEFAULT_CONVERSATION_MODEL

# Add a client reference for SDK operations
sdk_client = None

def init_sdk_client():
    """Initialize the LM Studio SDK client"""
    global sdk_client
    try:
        if sdk_client is None:
            sdk_client = lms.Client()
            print("LM Studio SDK client initialized", flush=True)
        return sdk_client
    except Exception as e:
        print(f"Error initializing LM Studio SDK client: {str(e)}", flush=True)
        return None

def get_sdk_model(model_id=None, temp_instance=False, instance_name=None):
    """
    Get a direct reference to an LM Studio model using SDK
    
    Args:
        model_id: The model identifier to load (if None, uses currently loaded model)
        temp_instance: If True, creates a new temporary instance
        instance_name: Optional name for the instance
        
    Returns:
        An LLM model instance or None if failed
    """
    try:
        client = init_sdk_client()
        if client is None:
            return None
            
        # If no model_id specified, use the currently loaded model
        if (model_id is None):
            model_id = get_loaded_model()
            if model_id is None:
                print("No model is currently loaded", flush=True)
                return None
        
        # Load the model - either as a new instance or get existing
        if temp_instance:
            # Create a new temporary instance
            print(f"Creating temporary instance of model: {model_id}", flush=True)
            return client.llm.load_new_instance(model_id, instance_name)
        else:
            # Get existing or load if not already loaded
            print(f"Getting or loading model: {model_id}", flush=True)
            return client.llm.model(model_id)
            
    except Exception as e:
        print(f"Error getting SDK model: {str(e)}", flush=True)
        return None

# Add new model management tools
LIST_MODELS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_available_models",
        "description": "List available LM Studio models and their specializations",
        "parameters": {"type": "object", "properties": {}}
    }
}

SELECT_MODEL_TOOL = {
    "type": "function",
    "function": {
        "name": "select_model",
        "description": "Select a specialized model for a specific task",
        "parameters": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string", 
                    "description": "The type of task to perform",
                    "enum": ["summarization", "analysis", "creative", "coding", "default"]
                }
            },
            "required": ["task_type"]
        }
    }
}

# Add new model loading tool
LOAD_MODEL_TOOL = {
    "type": "function",
    "function": {
        "name": "load_model",
        "description": "Load a specific model into LM Studio",
        "parameters": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "The model identifier to load"
                }
            },
            "required": ["model_id"]
        }
    }
}

UNLOAD_MODEL_TOOL = {
    "type": "function",
    "function": {
        "name": "unload_model",
        "description": "Unload a specific model from LM Studio",
        "parameters": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "The model identifier to unload"
                }
            },
            "required": ["model_id"]
        }
    }
}

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

BACKGROUND_CHECK_TOOL = {
    "type": "function",
    "function": {
        "name": "background_check",
        "description": "Perform a background check on a person and return detailed information.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the person to search for."}
            },
            "required": ["name"]
        }
    }
}

VOICE_TOOL = {
    "type": "function",
    "function": {
        "name": "listen_voice",
        "description": "Listen for voice input from microphone",
        "parameters": {"type": "object", "properties": {}}
    }
}

PDF_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_pdf",
        "description": "Extract and analyze text from a PDF file",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the PDF file"}
            },
            "required": ["filepath"]
        }
    }
}

YOUTUBE_TOOL = {
    "type": "function",
    "function": {
        "name": "summarize_youtube",
        "description": "Get transcript and summarize YouTube video",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string", "description": "YouTube video ID"}
            },
            "required": ["video_id"]
        }
    }
}

WEATHER_CURRENT_TOOL = {
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

WEATHER_FORCAST_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather_forcast",
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

TEXT_TO_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_image",
        "description": "Generate an image from text description using Stable Diffusion",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The text description of the image to generate"},
                "negative_prompt": {"type": "string", "description": "Things to avoid in the image", "default": ""},
                "steps": {"type": "integer", "description": "Number of sampling steps", "default": 20},
                "width": {"type": "integer", "description": "Image width", "default": 512},
                "height": {"type": "integer", "description": "Image height", "default": 512}
            },
            "required": ["prompt"]
        }
    }
}

OPEN_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "open_saved_image",
        "description": "List and open saved images from ./images and ./generated_images directories",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Either 'list' to show available images or 'open' to open a specific image"},
                "image_number": {"type": "integer", "description": "The number of the image to open from the list", "default": 0}
            },
            "required": ["action"]
        }
    }
}

SPEAK_TOOL = {
    "type": "function",
    "function": {
        "name": "speak_text",
        "description": "Convert text to speech and play it",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to convert to speech"}
            },
            "required": ["text"]
        }
    }
}

FILE_LIST_TOOL = {
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

FILE_MOVE_TOOL = {
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

FILE_COPY_TOOL = {
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

FILE_DELETE_TOOL = {
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

FILE_DOWNLOAD_TOOL = {
    "type": "function",
    "function": {
        "name": "download_file",
        "description": "Download a file directly from a URL to the local computer. This tool handles the download operation for you, no coding required.",
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

FILE_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_files",
        "description": "Search for files across drives or in a specific directory",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Filename pattern to search for (e.g., *.jpg, document.pdf)"},
                "location": {"type": "string", "description": "Optional: Directory to search in. Leave empty to search all available drives", "default": ""}
            },
            "required": ["pattern"]
        }
    }
}

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

FILE_ANALYZE_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_file",
        "description": "Extract and analyze content from various file types (text, CSV, JSON, code files, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to analyze"},
                "analysis_type": {
                    "type": "string", 
                    "description": "Type of analysis to perform",
                    "enum": ["content", "statistics", "structure", "summary", "auto"],
                    "default": "auto"
                }
            },
            "required": ["filepath"]
        }
    }
}

def get_current_time():
    return {"time": time.strftime("%H:%M:%S")}

def get_current_date():
    return {"date": time.strftime("%Y-%m-%d")}

def google_search(query):
    try:
        # Use a shorter pause time (2 seconds) and limit results to 3 to avoid timeouts
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
    if (os.path.exists(DOWNLOADED_DIR) and os.listdir(DOWNLOADED_DIR)):
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

def background_check(name):
    try:
        # Perform a Google search for the person's name
        search_results = google_search(name)
        if "error" in search_results:
            return search_results

        # Extract detailed information from the top search results
        details = []
        for url in search_results["results"]:
            webpage_content = read_webpage(url)
            if "error" not in webpage_content:
                details.append(webpage_content["content"])

        return {"details": details}
    except Exception as e:
        return {"error": f"Background check failed: {str(e)}"}

def listen_voice():
    """Listen for voice input and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...",flush=True)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return {"text": text}
        except Exception as e:
            return {"error": f"Voice recognition failed: {str(e)}"}

def speak_text(text):
    """Convert text to speech and play it"""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")
        if os.name == 'nt':  # Windows
            os.system("start response.mp3")
        else:  # Linux/Mac
            os.system("xdg-open response.mp3")
        return {"status": "Speech generated and played"}
    except Exception as e:
        return {"error": f"Speech generation failed: {str(e)}"}

def analyze_pdf(filepath):
    """Extract and analyze text from PDF"""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return {"content": text[:2000]}  # Limit content length
    except Exception as e:
        return {"error": f"PDF analysis failed: {str(e)}"}

def summarize_youtube(video_id):
    """Get and summarize YouTube video transcript"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry['text'] for entry in transcript])
        return {"transcript": full_text[:2000]}  # Limit content length
    except Exception as e:
        return {"error": f"YouTube transcript extraction failed: {str(e)}"}

def get_weather_current(location):
    # https://www.weatherapi.com/my/
    """Get weather information for a location"""
    # Replace with your preferred weather API
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
    try:
        response = requests.get(url)
        data = response.json()
        return {"weather": data}
    except Exception as e:
        return {"error": f"Weather lookup failed: {str(e)}"}
    
def get_weather_forcast(location):
    """Get weather information for a location"""
    # Replace with your preferred weather API
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"
    try:
        response = requests.get(url)
        data = response.json()
        return {"weather": data}
    except Exception as e:
        return {"error": f"Weather lookup failed: {str(e)}"}

def call_txt2img_api(payload):
    """Make API call to Stable Diffusion WebUI"""
    try:
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            f'{WEBUI_URL}/sdapi/v1/txt2img',
            headers={'Content-Type': 'application/json'},
            data=data
        )
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}

def generate_image(prompt, negative_prompt="", steps=20, width=512, height=512):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(GENERATED_DIR, exist_ok=True)

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M",
        "n_iter": 1,
        "batch_size": 1
    }

    response = call_txt2img_api(payload)
    if "error" in response:
        return response

    image_paths = []
    for index, image in enumerate(response.get('images', [])):
        save_path = os.path.join(GENERATED_DIR, f'generation-{timestamp}-{index}.png')
        try:
            with open(save_path, "wb") as file:
                file.write(base64.b64decode(image))
            image_paths.append(save_path)
        except Exception as e:
            return {"error": f"Failed to save image: {str(e)}"}

    return {"images": image_paths}

def list_available_images():
    """List all images in both directories with numbered indices"""
    images = []
    
    # Check generated images directory
    if os.path.exists(GENERATED_DIR):
        for file in os.listdir(GENERATED_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                images.append(os.path.join(GENERATED_DIR, file))
    
    # Check downloaded images directory
    if os.path.exists(DOWNLOADED_DIR):
        for file in os.listdir(DOWNLOADED_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                images.append(os.path.join(DOWNLOADED_DIR, file))
    
    # Check parent image directory
    if os.path.exists(IMAGE_DIR):
        for file in os.listdir(IMAGE_DIR):
            file_path = os.path.join(IMAGE_DIR, file)
            if os.path.isfile(file_path) and file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                images.append(file_path)
    
    if not images:
        return {"error": "No images found"}
    
    # Create numbered list of images
    image_list = []
    for i, path in enumerate(images, 1):
        image_list.append(f"{i}: {path}")
    
    return {"images": image_list, "paths": images}

def open_file(filepath):
    """Open any file with the system's default application"""
    try:
        filepath = os.path.expanduser(filepath)
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
        
        # Use platform-specific methods to open the file
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", filepath], check=True)
        else:  # Linux and other Unix
            subprocess.run(["xdg-open", filepath], check=True)
        
        return {"status": f"Successfully opened {filepath}"}
    except Exception as e:
        return {"error": f"Failed to open file: {str(e)}"}

def open_saved_image(action, image_number=0):
    """List available images or open a specific one (enhanced to handle any path)"""
    if action == "list":
        return list_available_images()
    
    elif action == "open":
        images_info = list_available_images()
        if "error" in images_info:
            return images_info
            
        if not 1 <= image_number <= len(images_info["paths"]):
            return {"error": f"Invalid image number. Please choose between 1 and {len(images_info['paths'])}"}
            
        try:
            image_path = images_info["paths"][image_number - 1]
            return open_file(image_path)  # Use the more robust open_file function
        except Exception as e:
            return {"error": f"Failed to open image: {str(e)}"}

def list_files(path, pattern="*"):
    """List files in a directory matching a pattern"""
    try:
        path = os.path.expanduser(path)  # Handle ~ in paths
        if not os.path.exists(path):
            return {"error": f"Directory not found: {path}"}
        
        files = []
        if pattern == "*":
            # Get both files and directories
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                item_type = "directory" if os.path.isdir(full_path) else "file"
                files.append({"name": item, "type": item_type, "path": full_path})
        else:
            # Use glob pattern
            for file_path in glob.glob(os.path.join(path, pattern)):
                item_type = "directory" if os.path.isdir(file_path) else "file"
                files.append({"name": os.path.basename(file_path), "type": item_type, "path": file_path})
        
        # Add disk information for root directory
        if os.path.abspath(path) == os.path.abspath(os.path.join(path, os.pardir)):
            if platform.system() == "Windows":
                import win32api
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    files.append({"name": drive, "type": "drive", "path": drive})
        
        return {"files": files}
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}

def move_file(source, destination):
    """Move a file from source to destination"""
    try:
        source = os.path.expanduser(source)
        destination = os.path.expanduser(destination)
        
        if not os.path.exists(source):
            return {"error": f"Source file not found: {source}"}
        
        # Create destination directory if needed
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        shutil.move(source, destination)
        return {"status": f"Successfully moved {source} to {destination}"}
    except Exception as e:
        return {"error": f"Failed to move file: {str(e)}"}

def copy_file(source, destination):
    """Copy a file from source to destination"""
    try:
        source = os.path.expanduser(source)
        destination = os.path.expanduser(destination)
        
        if not os.path.exists(source):
            return {"error": f"Source file not found: {source}"}
        
        # Create destination directory if needed
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return {"status": f"Successfully copied {source} to {destination}"}
    except Exception as e:
        return {"error": f"Failed to copy file: {str(e)}"}

def delete_file(path):
    """Delete a file or directory"""
    try:
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        
        if os.path.isdir(path):
            shutil.rmtree(path)
            return {"status": f"Successfully deleted directory: {path}"}
        else:
            os.remove(path)
            return {"status": f"Successfully deleted file: {path}"}
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}

def download_file(url, save_path):
    """Download a file from URL and save to path"""
    try:
        save_path = os.path.expanduser(save_path)
        
        # Create directory if needed
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # Download the file
        print(f"\nDownloading file from {url} to {save_path}...", flush=True)
        
        with urllib.request.urlopen(url) as response, open(save_path, 'wb') as out_file:
            file_size = response.headers.get('Content-Length')
            downloaded = 0
            
            # If we know the file size, show a simple progress
            if file_size:
                file_size = int(file_size)
                chunk_size = file_size // 10
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    progress = int((downloaded / file_size) * 100)
                    print(f"Download progress: {progress}%", flush=True)
            else:
                # If unknown file size, just copy
                shutil.copyfileobj(response, out_file)
        
        print(f"Download complete!", flush=True)
        return {"status": f"Successfully downloaded file to {save_path}", "downloaded": True, "path": save_path}
    except Exception as e:
        return {"error": f"Failed to download file: {str(e)}", "downloaded": False}

def search_files(pattern, location=""):
    """
    Search for files matching a pattern across drives or in a specific directory
    """
    try:
        results = []
        search_pattern = pattern.strip()
        
        if location:
            # Search in specified location
            location = os.path.expanduser(location)
            if not os.path.exists(location):
                return {"error": f"Location not found: {location}"}
            
            # Walk through directory tree
            for root, dirs, files in os.walk(location):
                for file in files:
                    if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                        file_path = os.path.join(root, file)
                        results.append(file_path)
                
                # Limit results to prevent overwhelming response
                if len(results) >= 50:
                    results.append("Search limited to 50 results. Please refine your search.")
                    break
        else:
            # Search across all drives on Windows
            if platform.system() == "Windows":
                try:
                    import win32api
                    drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                    
                    for drive in drives:
                        try:
                            # Search in user directories first for efficiency
                            if os.path.exists(os.path.join(drive, "Users")):
                                for root, dirs, files in os.walk(os.path.join(drive, "Users")):
                                    for file in files:
                                        if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                                            file_path = os.path.join(root, file)
                                            results.append(file_path)
                                    
                                    if len(results) >= 50:
                                        break
                            
                            # If we still need more results, do a broader search
                            if len(results) < 50:
                                # Skip Windows system directories for performance
                                for root, dirs, files in os.walk(drive):
                                    # Skip Windows system directories
                                    if any(skip in root.lower() for skip in ["windows", "program files", "$recycle.bin", "system volume information"]):
                                        continue
                                    
                                    for file in files:
                                        if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                                            file_path = os.path.join(root, file)
                                            results.append(file_path)
                                    
                                    if len(results) >= 50:
                                        break
                        except PermissionError:
                            pass  # Skip directories we can't access
                        except Exception as e:
                            print(f"Error searching {drive}: {str(e)}")
                except Exception as e:
                    return {"error": f"Error listing drives: {str(e)}"}
            else:
                # For Linux/macOS, search in home directory
                home_dir = os.path.expanduser("~")
                for root, dirs, files in os.walk(home_dir):
                    for file in files:
                        if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                            file_path = os.path.join(root, file)
                            results.append(file_path)
                    
                    if len(results) >= 50:
                        break
        
        if not results:
            return {"status": "No files found matching the pattern", "results": []}
        
        return {"status": f"Found {len(results)} files", "results": results[:50]}
    
    except Exception as e:
        return {"error": f"File search failed: {str(e)}"}

def analyze_file(filepath, analysis_type="auto"):
    """Extract and analyze content from various file types"""
    try:
        filepath = os.path.expanduser(filepath)
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
            
        # Determine file type
        file_extension = os.path.splitext(filepath)[1].lower()
        
        # Try to detect mime type
        mime_type, _ = mimetypes.guess_type(filepath)
        mime_category = mime_type.split('/')[0] if mime_type else None
        
        # Get file size
        file_size = os.path.getsize(filepath) / (1024 * 1024)  # Size in MB
        
        # For large files, warn about size
        if file_size > 50:
            return {"error": f"File is too large ({file_size:.2f} MB) for analysis. Please provide a smaller file."}
            
        # Detect text encoding first for text files
        encoding = 'utf-8'  # Default encoding
        if mime_category == 'text' or file_extension in ['.txt', '.py', '.js', '.html', '.css', '.json', '.csv', '.md', '.xml', '.log', '.ini', '.cfg', '.conf']:
            with open(filepath, 'rb') as f:
                raw_data = f.read(min(1000000, os.path.getsize(filepath)))  # Read at most 1MB
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
        
        # Process based on file type
        result = {}
        
        # Text files (including code files)
        if mime_category == 'text' or file_extension in ['.txt', '.py', '.js', '.html', '.css', '.md', '.log', '.ini', '.cfg', '.conf']:
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            # Basic content
            result["file_type"] = "text"
            result["extension"] = file_extension
            result["encoding"] = encoding
            result["size_mb"] = file_size
            
            # Lines and words count
            lines = content.split('\n')
            result["line_count"] = len(lines)
            result["word_count"] = len(content.split())
            result["char_count"] = len(content)
            
            # Different analysis based on requested type
            if analysis_type in ["content", "auto"]:
                # Limit content to avoid overwhelming responses
                if len(content) > 5000:
                    result["content_preview"] = content[:5000] + "... [content truncated]"
                else:
                    result["content"] = content
                    
            if analysis_type in ["statistics", "auto"]:
                # Get most common words
                words = [word.lower() for word in re.findall(r'\w+', content)]
                result["most_common_words"] = Counter(words).most_common(10)
                
                # Line length statistics
                line_lengths = [len(line) for line in lines]
                if line_lengths:
                    result["avg_line_length"] = sum(line_lengths) / len(line_lengths)
                    result["max_line_length"] = max(line_lengths)
                
            if analysis_type in ["structure", "summary"]:
                # For code files, extract structure info
                if file_extension in ['.py', '.js']:
                    # Simple function/class detection for Python/JavaScript
                    if file_extension == '.py':
                        function_matches = re.findall(r'def\s+(\w+)\s*\(', content)
                        class_matches = re.findall(r'class\s+(\w+)', content)
                    else:  # JavaScript
                        function_matches = re.findall(r'function\s+(\w+)\s*\(', content)
                        class_matches = re.findall(r'class\s+(\w+)', content)
                        
                    result["functions"] = function_matches
                    result["classes"] = class_matches
                    
                # For markdown files, extract headers
                elif file_extension == '.md':
                    headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
                    result["headers"] = headers
                
                # General structure - look for sections
                sections = re.findall(r'^[=\-#]+\s*(.+?)\s*[=\-#]+$', content, re.MULTILINE)
                if sections:
                    result["sections"] = sections
        
        # CSV files
        elif file_extension == '.csv':
            result["file_type"] = "csv"
            result["extension"] = file_extension
            result["size_mb"] = file_size
            
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader, [])
                rows = []
                row_count = 0
                
                # Get sample of data
                for i, row in enumerate(csv_reader):
                    row_count += 1
                    if i < 5:  # Only keep first 5 rows as sample
                        rows.append(row)
            
            result["headers"] = headers
            result["row_count"] = row_count + 1  # Include header row
            result["column_count"] = len(headers)
            
            if analysis_type in ["content", "auto", "summary"]:
                result["sample_rows"] = rows
                
            if analysis_type in ["statistics", "structure"]:
                # Try to infer column types
                column_types = []
                if rows:
                    for col_idx in range(len(headers)):
                        # Check only values that exist
                        col_values = [row[col_idx] for row in rows if col_idx < len(row)]
                        
                        # Try to determine if column is numeric, date, or text
                        numeric_count = sum(1 for val in col_values if re.match(r'^-?\d+(\.\d+)?$', val))
                        date_count = sum(1 for val in col_values if re.match(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', val))
                        
                        if numeric_count == len(col_values):
                            column_types.append("numeric")
                        elif date_count == len(col_values):
                            column_types.append("date")
                        else:
                            column_types.append("text")
                    
                    result["inferred_column_types"] = column_types
        
        # JSON files
        elif file_extension == '.json':
            result["file_type"] = "json"
            result["extension"] = file_extension
            result["size_mb"] = file_size
            
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                json_data = json_lib.load(f)
            
            if analysis_type in ["content", "auto"] and file_size < 1:  # Only include full content for small JSON files
                result["content"] = json_data
            
            if analysis_type in ["structure", "summary", "auto"]:
                # Analyze structure
                if isinstance(json_data, dict):
                    result["structure_type"] = "object"
                    result["top_level_keys"] = list(json_data.keys())
                    
                    # Sample nested structure if not too deep
                    if len(json_data) > 0:
                        sample_key = next(iter(json_data))
                        sample_value = json_data[sample_key]
                        if isinstance(sample_value, (dict, list)) and not too_complex(sample_value):
                            result["sample_nested_structure"] = sample_value
                            
                elif isinstance(json_data, list):
                    result["structure_type"] = "array"
                    result["array_length"] = len(json_data)
                    
                    # Get sample of first item if it's not too complex
                    if len(json_data) > 0 and not too_complex(json_data[0]):
                        result["sample_item"] = json_data[0]
                        
                        # If all items have same structure, note the keys
                        if all(isinstance(item, dict) for item in json_data[:5]):
                            keys_sets = [set(item.keys()) for item in json_data[:5]]
                            if all(keys_set == keys_sets[0] for keys_set in keys_sets):
                                result["common_keys"] = list(keys_sets[0])
        
        return result
    except Exception as e:
        return {"error": f"File analysis failed: {str(e)}"}

def too_complex(obj, depth=0, max_depth=3):
    """Helper to determine if an object is too complex to display in full"""
    if depth > max_depth:
        return True
        
    if isinstance(obj, dict):
        if len(obj) > 10:  # Too many keys
            return True
        return any(too_complex(v, depth+1, max_depth) for v in list(obj.values())[:5])
    
    elif isinstance(obj, list):
        if len(obj) > 10:  # Too many items
            return True
        return any(too_complex(v, depth+1, max_depth) for v in obj[:5])
        
    return False

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
                print(flush=True)
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
                        "id": "", "type": "function",
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

def execute_tool_call(tool_call, messages):
    """Execute a single tool call and append result to messages"""
    try:
        query_args = json.loads(tool_call["function"]["arguments"])
        query = query_args.get("query", "")
    except json.JSONDecodeError:
        print("Error: Invalid JSON arguments.", flush=True)
        result = {"error": "Invalid JSON arguments."}
        messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]})
        return messages, None

    # Handle model management tools
    if tool_call["function"]["name"] == "list_available_models":
        result = list_available_models()
    elif tool_call["function"]["name"] == "select_model":
        result = select_model(query_args["task_type"])
        print(f"\nSwitched specialized model to: {query_args['task_type']} ({AVAILABLE_SPECIALIZED_MODELS[query_args['task_type']]})", flush=True)
    # Add handlers for new load/unload model tools
    elif tool_call["function"]["name"] == "load_model":
        # Run async function using asyncio
        result = asyncio.run(load_model(query_args["model_id"]))
    elif tool_call["function"]["name"] == "unload_model":
        # Run async function using asyncio
        result = asyncio.run(unload_model(query_args["model_id"]))
    # Handle all other existing tools
    elif tool_call["function"]["name"] == "get_current_time":
        result = get_current_time()
    elif tool_call["function"]["name"] == "get_current_date":
        result = get_current_date()
    elif tool_call["function"]["name"] == "google_search":
        result = google_search(query)
    elif tool_call["function"]["name"] == "google_image_search":
        result = google_image_search(query)
        if result.get("status") == "confirm_override":
            return messages, {"query": result["query"], "tool_call_id": tool_call["id"]}
    elif tool_call["function"]["name"] == "read_webpage":
        result = read_webpage(query_args["url"])
    elif tool_call["function"]["name"] == "background_check":
        result = background_check(query_args["name"])
    elif tool_call["function"]["name"] == "listen_voice":
        result = listen_voice()
    elif tool_call["function"]["name"] == "analyze_pdf":
        result = analyze_pdf(query_args["filepath"])
    elif tool_call["function"]["name"] == "summarize_youtube":
        result = summarize_youtube(query_args["video_id"])
    elif tool_call["function"]["name"] == "get_weather":
        result = get_weather_current(query_args["location"])
    elif tool_call["function"]["name"] == "get_weather_forcast":
        result = get_weather_forcast(query_args["location"])
    elif tool_call["function"]["name"] == "generate_image":
        result = generate_image(**query_args)
    elif tool_call["function"]["name"] == "open_saved_image":
        result = open_saved_image(**query_args)
    elif tool_call["function"]["name"] == "speak_text":
        result = speak_text(**query_args)
    elif tool_call["function"]["name"] == "list_files":
        result = list_files(**query_args)
    elif tool_call["function"]["name"] == "move_file":
        result = move_file(**query_args)
    elif tool_call["function"]["name"] == "copy_file":
        result = copy_file(**query_args)
    elif tool_call["function"]["name"] == "delete_file":
        result = delete_file(**query_args)
    elif tool_call["function"]["name"] == "download_file":
        result = download_file(**query_args)
    elif tool_call["function"]["name"] == "search_files":
        result = search_files(**query_args)
    elif tool_call["function"]["name"] == "open_file":
        result = open_file(**query_args)
    elif tool_call["function"]["name"] == "analyze_file":
        result = analyze_file(**query_args)
    else:
        result = {"error": f"Unknown tool: {tool_call['function']['name']}"}

    messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]})
    return messages, None

def process_tool_calls(tool_calls, messages):
    """Process multiple tool calls sequentially"""
    pending_image_query = None
    
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        print(f"**Calling Tool: {tool_name}**", flush=True)
        
        # Execute the tool call
        messages, pending = execute_tool_call(tool_call, messages)
        if pending:
            pending_image_query = pending
            break

    return messages, pending_image_query

def check_loaded_models():
    """List all loaded models using the SDK"""
    try:
        client = init_sdk_client()
        if client is None:
            return {"error": "SDK client initialization failed"}
            
        # List all loaded models
        all_models = [m.identifier for m in client.llm.list_loaded()]
        print("All loaded models:", all_models)

        # List loaded embedding models
        embedding_models = [m.identifier for m in client.embedding.list_loaded()]
        print("Loaded embedding models:", embedding_models)

        # List loaded LLMs
        llms = [m.identifier for m in client.llm.list_loaded()]
        print("Loaded LLMs:", llms)
        
        return {
            "all_models": all_models,
            "embedding_models": embedding_models,
            "llm_models": llms
        }
    except Exception as e:
        print(f"Error checking loaded models: {str(e)}", flush=True)
        return {
            "all_models": [],
            "embedding_models": [],
            "llm_models": []
        }

def get_loaded_model():
    """Get information about the currently loaded model in LM Studio using SDK"""
    try:
        client = init_sdk_client()
        if client:
            # Get loaded LLMs using the SDK
            llms = [m.identifier for m in client.llm.list_loaded()]
            
            # Return the first loaded LLM, if any
            if llms:
                return llms[0]
        
        # Fallback to API detection if SDK fails or no LLMs found
        response = client.chat.completions.create(
            model="",  # No specific model requested, will use default loaded model
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        if hasattr(response, 'model') and response.model:
            return response.model
        
        # If the model attribute is not present or empty, try the raw response
        model_info = response.model_dump()
        if 'model' in model_info and model_info['model']:
            return model_info['model']
        
        return None
    except Exception as e:
        print(f"Failed to get loaded model: {str(e)}", flush=True)
        return None

def fetch_available_api_models():
    """Fetch available models from the LM Studio API and local installation"""
    global API_MODELS, AVAILABLE_SPECIALIZED_MODELS, DEFAULT_CONVERSATION_MODEL, CURRENTLY_LOADED_MODEL
    
    models = []
    
    try:
        # First get online API models
        response = requests.get(f"{LMSTUDIO_API_BASE}/models")
        models_data = response.json()
        api_models = [model["id"] for model in models_data.get("data", [])]
        
        # Then get local models using SDK instead of CLI
        try:
            local_models = [m.identifier for m in lms.list_models()]
        except:
            local_models = []
            print("SDK list_models failed, using API models only", flush=True)
        
        # Combine both lists, prioritizing local models
        models = list(set(api_models + local_models))
        API_MODELS = models
        
        # Filter out vocab files and embedding models
        valid_models = [m for m in models 
                       if not (m.startswith("llama.cpp/models/ggml-vocab") 
                              or m.startswith("text-embedding")
                              or ".gguf" in m)]
        
        print(f"Found {len(valid_models)} usable models:", flush=True)
        for model in valid_models:
            print(f"  - {model}", flush=True)
        
        # Auto-categorize available models
        for model_id in valid_models:
            model_lower = model_id.lower()
            
            # First check if we already have a qwen model for conversation
            if "qwen" in model_lower and "instruct" in model_lower:
                DEFAULT_CONVERSATION_MODEL = model_id
                AVAILABLE_SPECIALIZED_MODELS["default"] = model_id
            
            # Categorize models by likely specialties
            if "mistral" in model_lower or "mixtral" in model_lower:
                AVAILABLE_SPECIALIZED_MODELS["summarization"] = model_id
            elif "llama" in model_lower and "instruct" in model_lower:
                AVAILABLE_SPECIALIZED_MODELS["analysis"] = model_id
            elif any(term in model_lower for term in ["gemma", "neural-chat", "phi"]):
                AVAILABLE_SPECIALIZED_MODELS["creative"] = model_id
            elif any(term in model_lower for term in ["coder", "deepseek", "starcoder", "function"]):
                AVAILABLE_SPECIALIZED_MODELS["coding"] = model_id
            elif "functionary" in model_lower or "gorilla-openfunctions" in model_lower:
                # Special handling for models explicitly designed for function calling
                DEFAULT_CONVERSATION_MODEL = model_id
                AVAILABLE_SPECIALIZED_MODELS["default"] = model_id
        
        # Set MODEL to DEFAULT_CONVERSATION_MODEL
        global MODEL
        MODEL = DEFAULT_CONVERSATION_MODEL
        
        # Check which model is currently loaded using SDK
        CURRENTLY_LOADED_MODEL = get_loaded_model()
        print(f"Currently loaded model: {CURRENTLY_LOADED_MODEL}", flush=True)
        
        return True
    except Exception as e:
        print(f"Error fetching models: {str(e)}", flush=True)
        return False

def categorize_model(model_id):
    """Determine the likely purpose/category of a model based on its name"""
    model_lower = model_id.lower()
    
    # Determine model category
    if "qwen" in model_lower or "functionary" in model_lower or "gorilla-openfunct" in model_lower:
        return "default", "General purpose model with good tool/function usage"
    elif "mistral" in model_lower or "mixtral" in model_lower:
        return "summarization", "Good for summarization tasks"
    elif "llama" in model_lower and ("3" in model_lower or "instruct" in model_lower):
        return "analysis", "Good for analytical reasoning"
    elif any(term in model_lower for term in ["gemma"]):
        return "creative", "Good for creative content generation"
    elif any(term in model_lower for term in ["coder", "deepseek", "starcoder", "code"]):
        return "coding", "Specialized for code generation and programming tasks"
    elif "llava" in model_lower:
        return "vision", "Vision capabilities for image analysis"
    else:
        return "general", "General purpose language model"

def list_available_models():
    """List all available models and their specializations"""
    # First refresh the list of loaded models using SDK
    loaded_models_info = check_loaded_models()
    
    models = {
        "current_conversation_model": DEFAULT_CONVERSATION_MODEL,
        "current_specialized_model": CURRENT_SPECIALIZED_MODEL,
        "currently_loaded_model": CURRENTLY_LOADED_MODEL,
        "loaded_models": loaded_models_info,
        "available_specialized_models": {},
        "api_models": {}
    }
    
    # Add specialized models with descriptions
    for task_type, model_name in AVAILABLE_SPECIALIZED_MODELS.items():
        category, description = categorize_model(model_name)
        models["available_specialized_models"][task_type] = {
            "name": model_name,
            "description": description,
            "is_loaded": model_name in loaded_models_info["llm_models"]
        }
    
    # Add all API models
    for model_name in API_MODELS:
        category, description = categorize_model(model_name)
        models["api_models"][model_name] = {
            "type": category,
            "description": description,
            "is_loaded": model_name in loaded_models_info["all_models"]
        }
    
    return models

def select_model(task_type):
    """Select a model based on the task type"""
    global CURRENT_SPECIALIZED_MODEL, CURRENTLY_LOADED_MODEL
    
    if task_type not in AVAILABLE_SPECIALIZED_MODELS:
        return {"status": "error", "message": f"Unknown task type: {task_type}"}
    
    # Store previously selected model
    previous_model = CURRENT_SPECIALIZED_MODEL
    
    # Update current specialized model
    CURRENT_SPECIALIZED_MODEL = task_type
    model_id = AVAILABLE_SPECIALIZED_MODELS[task_type]
    
    # Check if we need to load a different model
    if CURRENTLY_LOADED_MODEL != model_id:
        print(f"Selected model {model_id} for {task_type} tasks", flush=True)
        print(f"To actually load this model, use the load_model tool.", flush=True)
        
        # We could automatically load the model here, but we'll make it explicit
        # asyncio.run(load_model(model_id))
    else:
        print(f"Model {model_id} is already loaded for {task_type} tasks", flush=True)
    
    return {
        "status": "success", 
        "previous_task_type": previous_model,
        "new_task_type": task_type,
        "model": model_id,
        "already_loaded": CURRENTLY_LOADED_MODEL == model_id,
        "note": "To actually load this model, use the load_model tool."
    }

def get_model_for_task(task=None):
    """Return the appropriate model name based on current task"""
    if task == "conversation" or task is None:
        return DEFAULT_CONVERSATION_MODEL
    else:
        return AVAILABLE_SPECIALIZED_MODELS[CURRENT_SPECIALIZED_MODEL]

def execute_with_specialized_model(messages, temperature=0.7):
    """Execute a request with the currently selected specialized model (conceptually)"""
    global CURRENTLY_LOADED_MODEL
    
    specialized_model = AVAILABLE_SPECIALIZED_MODELS[CURRENT_SPECIALIZED_MODEL]
    
    # We're not actually switching models, just using whatever is loaded
    actual_model = CURRENTLY_LOADED_MODEL or specialized_model
    
    # Display a note about which model is actually being used
    print(f"Using currently loaded model: {actual_model}", flush=True)
    print(f"Note: This is a {CURRENT_SPECIALIZED_MODEL} task that would ideally use {specialized_model}", flush=True)
    
    # Use the API to get a response
    try:
        completion = client.chat.completions.create(
            model=actual_model,  # This will use whatever model is currently loaded
            messages=messages,
            temperature=temperature
        )
        result = completion.choices[0].message.content
        return result
    except Exception as e:
        error_msg = f"Error using model: {str(e)}"
        print(error_msg, flush=True)
        return f"{error_msg}. Please check your LM Studio configuration."

def perform_specialized_task(task_type, content, messages):
    """Process content using a specialized model for a specific task (conceptually)"""
    # Select the specialized model (virtually only)
    select_model(task_type)
    model_name = AVAILABLE_SPECIALIZED_MODELS[task_type]
    
    # Create a simplified message list for the specialized task
    specialized_messages = [
        {"role": "system", "content": f"You are a specialized AI for {task_type} tasks."},
        {"role": "user", "content": content}
    ]
    
    print(f"\nProcessing {task_type} task with model {model_name} (virtual selection)...", flush=True)
    result = execute_with_specialized_model(specialized_messages)
    
    # Add the result to the main chat
    print(f"\nResponse:", flush=True)
    print(result, flush=True)
    
    # Return to the default model (virtually)
    select_model("default")
    
    return result

def check_lms_cli_available():
    """Check if the LM Studio SDK is properly working"""
    try:
        # Try to list loaded models using SDK instead of CLI
        lms.list_loaded_models()
        print("LM Studio SDK is working correctly", flush=True)
        return True
    except Exception as e:
        print(f"Error checking LM Studio SDK: {str(e)}", flush=True)
        return False

def list_local_models():
    """List all local models available in LM Studio using SDK"""
    try:
        # Use SDK instead of CLI
        models = [m.identifier for m in lms.list_models()]
        return models
    except Exception as e:
        print(f"Failed to list local models: {str(e)}", flush=True)
        return []

async def unload_model(model_id):
    """Unload a model using LM Studio SDK"""
    try:
        print(f"\nUnloading model: {model_id}...", flush=True)
        client = init_sdk_client()
        if client:
            await client.llm.unload(model_id)
            await client.embedding.unload(model_id)
            print(f"Successfully unloaded model: {model_id}", flush=True)
            return {"status": "success", "message": f"Model {model_id} unloaded successfully"}
        else:
            return {"status": "error", "message": "SDK client initialization failed"}
    except Exception as e:
        error_msg = f"Failed to unload model: {str(e)}"
        print(error_msg, flush=True)
        return {"status": "error", "message": error_msg}

async def load_model(model_id, temp_instance=False, instance_name=None):
    """
    Load a model using LM Studio SDK
    
    Args:
        model_id: The model identifier to load
        temp_instance: If True, creates a new temporary instance
        instance_name: Optional name for the instance
    """
    try:
        global CURRENTLY_LOADED_MODEL
        print(f"\nLoading model: {model_id}...", flush=True)
        
        client = init_sdk_client()
        if client is None:
            return {"status": "error", "message": "SDK client initialization failed"}
            
        LLM_LOAD_CONFIG = lms.LlmLoadModelConfig(seed=11434)
        
        if temp_instance:
            # Create a temporary instance - don't update CURRENTLY_LOADED_MODEL
            print(f"Creating temporary instance of model: {model_id}", flush=True)
            await client.llm.load_new_instance(model_id, 
                                              instance_name or f"temp-{int(time.time())}", 
                                              config=LLM_LOAD_CONFIG)
            return {"status": "success", 
                    "message": f"Temporary instance of model {model_id} loaded successfully",
                    "instance_name": instance_name,
                    "temp": True}
        else:
            # Load as the main model
            if model_id != CURRENTLY_LOADED_MODEL:
                model = await client.llm.load_new_instance(model_id, config=LLM_LOAD_CONFIG, ttl=None)
                # Also try to load embedding model if available
                try:
                    await client.embedding.load_new_instance(model_id, ttl=None)
                except:
                    print(f"No embedding model available for {model_id}", flush=True)
                
                CURRENTLY_LOADED_MODEL = model_id
                print(f"Successfully loaded model: {model_id}", flush=True)
                return {"status": "success", "message": f"Model {model_id} loaded successfully"}
            else:
                print(f"Model {model_id} is already loaded", flush=True)
                return {"status": "success", "message": f"Model {model_id} is already loaded"}
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        print(error_msg, flush=True)
        return {"status": "error", "message": error_msg}

def chat_with_tools(messages, model_id=None, temp_instance=False):
    """
    Use the LM Studio SDK to chat with multiple tools enabled
    
    Args:
        messages: The conversation history
        model_id: Optional specific model to use (if None, uses current model)
        temp_instance: If True, creates a temporary model instance
    """
    try:
        # Get or load the specified model
        sdk_model = get_sdk_model(model_id, temp_instance)
        if sdk_model is None:
            # Fall back to API if SDK model isn't available
            return use_openai_api_tools(messages)
        
        # Extract the last user message
        user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        if not user_message:
            return "I don't see a question to respond to."
        
        # Create a chat history context
        chat_history = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                chat_history.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                chat_history.append({"role": "assistant", "content": msg["content"]})
        
        # Create a chat object with system message if available
        if system_message:
            chat = lms.Chat(system_message)
        else:
            chat = lms.Chat()
        
        # Add previous messages to chat history
        for msg in chat_history[:-1]:  # Skip the last user message, we'll add it later
            if msg["role"] == "user":
                chat.add_user_message(msg["content"])
            else:
                chat.add_assistant_message(msg["content"])
        
        # Define typed tool functions for the SDK
        def get_time() -> dict:
            """Get the current time"""
            return {"time": time.strftime("%H:%M:%S")}
            
        def get_date() -> dict:
            """Get the current date"""
            return {"date": time.strftime("%Y-%m-%d")}
            
        def search(query: str) -> dict:
            """Search the web for information"""
            return google_search(query)
        
        def search_web_image(query: str) -> dict:
            """Search for images on the web"""
            result = google_image_search(query)
            # Handle confirmation needed differently for SDK tools
            if result.get("status") == "confirm_override":
                return {"status": "needs_confirmation", 
                        "message": "There are existing images. Would you like to override them?",
                        "query": result["query"]}
            return result
            
        def read_web_page(url: str) -> dict:
            """Read and summarize content from a webpage"""
            return read_webpage(url)
            
        def get_weather_info(location: str) -> dict:
            """Get current weather for a location"""
            return get_weather_current(location)
        
        # Add more tool functions as needed
        
        # Combine all tool functions
        tools = [
            get_time,
            get_date,
            search,
            search_web_image,
            read_web_page,
            get_weather_info
        ]
        
        # Collect response
        response_text = ""
        def collect_fragment(fragment, _=0):
            nonlocal response_text
            if fragment.content:
                print(fragment.content, end="", flush=True)
                response_text += fragment.content
        
        # Add the last user message and get a response with tools
        chat.add_user_message(user_message)
        print("\nAssistant: ", end="", flush=True)
        
        # Call the model with tools
        sdk_model.act(
            chat,
            tools,
            on_message=chat.append,
            on_prediction_fragment=collect_fragment
        )
        
        print()  # Add newline after response
        
        # If using a temporary instance, attempt to unload it to free resources
        if temp_instance and hasattr(sdk_model, 'instance_name'):
            try:
                asyncio.run(unload_model(sdk_model.instance_name))
            except Exception as e:
                print(f"Warning: Could not unload temporary model: {str(e)}", flush=True)
        
        # Return the full response text
        return response_text
    
    except Exception as e:
        print(f"Error using LM Studio SDK tools: {str(e)}", flush=True)
        # Fall back to OpenAI API if SDK fails
        return use_openai_api_tools(messages)

def use_openai_api_tools(messages):
    """Fall back to OpenAI API for tool calls if SDK method fails"""
    try:
        response_text, tool_calls = process_stream(
            client.chat.completions.create(
                model=DEFAULT_CONVERSATION_MODEL,
                messages=messages,
                tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, 
                       GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL, BACKGROUND_CHECK_TOOL,
                       VOICE_TOOL, PDF_TOOL, YOUTUBE_TOOL, WEATHER_CURRENT_TOOL, 
                       TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, SPEAK_TOOL, WEATHER_FORCAST_TOOL,
                       FILE_LIST_TOOL, FILE_MOVE_TOOL, FILE_COPY_TOOL, FILE_DELETE_TOOL, 
                       FILE_DOWNLOAD_TOOL, FILE_SEARCH_TOOL, OPEN_FILE_TOOL, FILE_ANALYZE_TOOL,
                       LIST_MODELS_TOOL, SELECT_MODEL_TOOL, LOAD_MODEL_TOOL, UNLOAD_MODEL_TOOL],
                stream=True,
                temperature=0.2
            )
        )
        
        return response_text, tool_calls
    except Exception as e:
        print(f"Error using OpenAI API for tools: {str(e)}", flush=True)
        return f"I encountered an error while trying to use tools: {str(e)}", []

def chat_loop():
    global CURRENTLY_LOADED_MODEL, DEFAULT_CONVERSATION_MODEL, sdk_client
    
    # Initialize the SDK client
    sdk_client = init_sdk_client()
    
    # Check which model is actually loaded
    CURRENTLY_LOADED_MODEL = get_loaded_model()
    print(f"Currently loaded model: {CURRENTLY_LOADED_MODEL}", flush=True)
    
    # If the actual model is different from what we want, just note it
    if CURRENTLY_LOADED_MODEL != DEFAULT_CONVERSATION_MODEL:
        print(f"Note: The loaded model ({CURRENTLY_LOADED_MODEL}) is different from the default conversation model ({DEFAULT_CONVERSATION_MODEL}).", flush=True)
        print("Will continue using the currently loaded model.", flush=True)
    
    messages = []
    pending_image_query = None
    
    # Get SDK model reference for direct tool calling
    sdk_model = get_sdk_model()
    if sdk_model:
        print(f"Successfully initialized LM Studio SDK with model: {CURRENTLY_LOADED_MODEL}", flush=True)
        print("Using native LM Studio tool calling capabilities", flush=True)
    else:
        print("Could not initialize LM Studio SDK for direct tool calling", flush=True)
        print("Falling back to OpenAI-compatible API for tool calls", flush=True)
    
    # Fix the system prompt format - combine multiple parts into a single string
    multiple_tools_note = "" if ALLOW_MULTIPLE_TOOL_CALLS else "You can only call 1 tool at a time! Please use 2 requests to do multiple tools."
    
    system_prompt = {
        "role": "system", 
        "content": (
            f"You are an AI assistant with access to various tools that can perform real actions. "
            f"Ask the user what their PC username is so you can find the right files. {multiple_tools_note} "
            f"When asked to download files, search for files, or open files, you can actually perform these "
            f"operations using your tools rather than explaining how to do them. "
            f"To use these specialized models, first call select_model, then call load_model to actually load it. "
            f"When user says to load a model please list models first to see available models, then load which one they are asking. "
            f"If it's already loaded use that for the chat! If not unload the models loaded and load the new model they want."
        )
    }
    
    messages.append(system_prompt)
    
    multiple_tools_status = "enabled" if ALLOW_MULTIPLE_TOOL_CALLS else "disabled"
    print(f"\n\nAssistant: Hi! I am an AI agent with various tools. Multiple tool calls are {multiple_tools_status}. Type 'quit' to exit or 'shutdown' to stop the server.", flush=True)
    print(f"Chatting with loaded model: {CURRENTLY_LOADED_MODEL}", flush=True)
    print(f"\nType 'list models' to see all available models, 'refresh models' to refresh the list.", flush=True)
    print(f"Type 'use model [model_name]' to switch models.", flush=True)
    print(f"Type 'load model [model_name]' to actually load a model using the SDK.", flush=True)

    while True:
        user_input = input("\nYou: ").strip()
        
        # Check for direct model commands
        if user_input.lower() == "list models":
            # Refresh the model list before displaying
            fetch_available_api_models()
            
            print("\nAvailable Models:", flush=True)
            print(f"Currently loaded model: {get_loaded_model()}", flush=True)
            print(f"Conversation model: {DEFAULT_CONVERSATION_MODEL}", flush=True)
            print(f"Current specialized task: {CURRENT_SPECIALIZED_MODEL}", flush=True)
            
            print("\nLocal models:", flush=True)
            for model in list_local_models():
                if model == get_loaded_model():
                    print(f"- {model} (LOADED)", flush=True)
                else:
                    print(f"- {model}", flush=True)
                    
            print("\nSpecialized models by task type:", flush=True)
            for task, model_name in AVAILABLE_SPECIALIZED_MODELS.items():
                category, description = categorize_model(model_name)
                print(f"- {task}: {model_name} - {description}", flush=True)
            
            continue
        elif user_input.lower() == "refresh models":
            print("Refreshing models...", flush=True)
            fetch_available_api_models()
            continue
        elif user_input.lower() == "show loaded model":
            current = get_loaded_model()
            print(f"Currently loaded model: {current}", flush=True)
            continue
        elif user_input.lower().startswith("use model "):
            model_name = user_input[10:].strip()
            
            # Check if it's a task type first
            if model_name in AVAILABLE_SPECIALIZED_MODELS:
                task_type = model_name
                model_id = AVAILABLE_SPECIALIZED_MODELS[task_type]
                result = select_model(task_type)
                print(f"\nVirtually switched to model: {model_id} for {task_type} tasks", flush=True)
                print("Note: The actual model loaded in LM Studio hasn't changed.", flush=True)
                    
            # Check if it's a specific model name
            elif model_name in API_MODELS or model_name in list_local_models():
                # Just update our internal tracking
                category, _ = categorize_model(model_name)
                AVAILABLE_SPECIALIZED_MODELS[category] = model_name
                if category == "default":
                    DEFAULT_CONVERSATION_MODEL = model_name
                print(f"\nVirtually switched to model: {model_name} for {category} tasks", flush=True)
                print("Note: The actual model loaded in LM Studio hasn't changed.", flush=True)
            else:
                print(f"\nUnknown model or task type: {model_name}", flush=True)
                print(f"Available task types: {', '.join(AVAILABLE_SPECIALIZED_MODELS.keys())}", flush=True)
                print(f"Use 'list models' to see all available models", flush=True)
            continue
        # Add direct load model command
        elif user_input.lower().startswith("load model "):
            model_name = user_input[11:].strip()
            if model_name in API_MODELS or model_name in list_local_models():
                print(f"\nLoading model: {model_name}...", flush=True)
                result = asyncio.run(load_model(model_name))
                if result["status"] == "success":
                    print(f"Successfully loaded model: {model_name}", flush=True)
                else:
                    print(f"Failed to load model: {result['message']}", flush=True)
            else:
                print(f"\nUnknown model: {model_name}", flush=True)
                print(f"Use 'list models' to see all available models", flush=True)
            continue
        elif user_input.lower() == "quit" or user_input.lower() == "shutdown":
            break

        # Handle pending image override confirmation
        if pending_image_query:
            if user_input.lower() in ['yes', 'y']:
                result = perform_image_search(pending_image_query["query"], override=True)
                messages.append({"role": "tool", "content": str(result), "tool_call_id": pending_image_query["tool_call_id"]})
            elif user_input.lower() in ['no', 'n']:
                result = perform_image_search(pending_image_query["query"], override=False)
                messages.append({"role": "tool", "content": str(result), "tool_call_id": pending_image_query["tool_call_id"]})
            pending_image_query = None
            continue

        # Check for direct specialized processing commands
        if user_input.lower().startswith("summarize:"):
            content = user_input[10:].trip()
            result = perform_specialized_task("summarization", content, messages)
            continue
        elif user_input.lower().startswith("analyze:"):
            content = user_input[8:].trip()
            result = perform_specialized_task("analysis", content, messages)
            continue
        elif user_input.lower().startswith("creative:"):
            content = user_input[9:].strip()
            result = perform_specialized_task("creative", content, messages)
            continue
        elif user_input.lower().startswith("code:"):
            content = user_input[5:].strip()
            result = perform_specialized_task("coding", content, messages)
            continue

        messages.append({"role": "user", "content": user_input})

        if ALLOW_MULTIPLE_TOOL_CALLS and sdk_model:
            # Use the SDK approach for multiple tool calling if available
            try:
                # Decide whether to use a temporary instance or not based on task complexity
                use_temp_instance = False  # For regular conversations, use the main model
                
                # Check if user is asking for a temporary task
                is_temp_task = any(keyword in user_input.lower() for keyword in [
                    "quick", "temporary", "once", "just this", "single", "one time", "this time"
                ])
                
                if is_temp_task:
                    use_temp_instance = True
                    print("Using temporary model instance for this task", flush=True)
                
                response_text = chat_with_tools(messages, model_id=None, temp_instance=use_temp_instance)
                messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                print(f"\nError using SDK for tool calls: {str(e)}", flush=True)
                print("Falling back to OpenAI API method", flush=True)
                
                # Fall back to OpenAI API method
                response_text, tool_calls = use_openai_api_tools(messages)
                
                # Process response and tool calls as before
                if len(response_text) > 0:
                    messages.append({"role": "assistant", "content": response_text})

                # Handle tool calls if any
                if tool_calls:
                    print(flush=True)
                    if len(response_text) == 0:
                        print("Assistant:", end=" ", flush=True)
                    
                    # Add tool calls to messages
                    messages.append({"role": "assistant", "tool_calls": tool_calls})
                    
                    # Process all tool calls sequentially
                    messages, pending_image_query = process_tool_calls(tool_calls, messages)
                    if pending_image_query:
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)", flush=True)
                        continue
                    
                    # Get final response after tool execution
                    final_response, _ = process_stream(
                        client.chat.completions.create(
                            model=DEFAULT_CONVERSATION_MODEL,
                            messages=messages,
                            stream=True
                        ),
                        add_assistant_label=False
                    )
                    
                    if final_response:
                        print(flush=True)
                        messages.append({"role": "assistant", "content": final_response})
        else:
            # Use the original OpenAI API compatible approach
            response_text, tool_calls = use_openai_api_tools(messages)

            if not tool_calls:
                print(flush=True)

            text_in_first_response = len(response_text) > 0
            if text_in_first_response:
                messages.append({"role": "assistant", "content": response_text})

            # Handle tool calls if any
            if tool_calls:
                print(flush=True)
                if not text_in_first_response:
                    print("Assistant:", end=" ", flush=True)
                
                # Add tool calls to messages
                messages.append({"role": "assistant", "tool_calls": tool_calls})

                # Process tool calls based on the setting
                if ALLOW_MULTIPLE_TOOL_CALLS:
                    # Process all tool calls sequentially
                    messages, pending_image_query = process_tool_calls(tool_calls, messages)
                    if pending_image_query:
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)", flush=True)
                        continue
                else:
                    # Original behavior: only process the first tool call
                    messages, pending_image_query = process_tool_calls([tool_calls[0]], messages)
                    if pending_image_query:
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)", flush=True)
                        continue

                # Get final response after tool execution - always use conversation model
                final_response, _ = process_stream(
                    client.chat.completions.create(
                        model=DEFAULT_CONVERSATION_MODEL,
                        messages=messages,
                        stream=True
                    ),
                    add_assistant_label=False
                )

                if final_response:
                    print(flush=True)
                    messages.append({"role": "assistant", "content": final_response})

# Clean up SDK client on exit
def cleanup():
    global sdk_client
    if sdk_client:
        try:
            sdk_client.close()
            print("SDK client closed", flush=True)
        except:
            pass

if __name__ == "__main__":
    # Check if LM Studio SDK is working 
    has_lms_sdk = check_lms_cli_available()

    if not has_lms_sdk:
        # Fetch models from API
        print(f"Fetching available models...", flush=True)
        if not fetch_available_api_models():
            print("Using default model settings instead.", flush=True)
    
    
    
    # # Check if LM Studio API is available
    # try:
    #     # Check which model is currently loaded (if any)
    #     current_model = get_loaded_model()
    #     if (current_model):
    #         CURRENTLY_LOADED_MODEL = current_model
    #         print(f"Currently loaded model: {CURRENTLY_LOADED_MODEL}", flush=True)
    #     else:
    #         print("Unable to determine the currently loaded model.", flush=True)
    #         print("Please ensure a model is loaded in LM Studio UI.", flush=True)
    # except Exception as e:
    #     print(f"Error connecting to LM Studio API at {LMSTUDIO_API_BASE}: {str(e)}", flush=True)
    #     print("Please ensure LM Studio is running and the API is enabled.", flush=True)
    #     sys.exit(1)
        
    try:
        chat_loop()
    finally:
        cleanup()