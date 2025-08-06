import os
import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler

# Tool definitions
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


# Tool implementations
def google_search(query):
    try:
        # Use a shorter pause time and limit results to 3 to avoid timeouts
        results = list(search(query, num=3, pause=2.0, stop=3))
        return {"results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}

def handle_image_files(query, override=False):
    """Helper function to manage image files"""
    DOWNLOADED_DIR = "./images/downloaded_images"
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
    DOWNLOADED_DIR = "./images/downloaded_images"
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

# Export tools
tools = [GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL, DOWNLOAD_FILE_TOOL]
tool_functions = {
    "google_search": google_search,
    "google_image_search": google_image_search,
    "read_webpage": read_webpage,
    "download_file": download_file,
}
