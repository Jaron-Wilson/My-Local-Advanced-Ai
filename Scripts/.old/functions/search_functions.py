"""
Web search related function implementations
"""
import os
import time
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler
from ..tools.config import DOWNLOADED_DIR

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

def google_search(query):
    """Perform a Google search and return top results"""
    try:
        # Use a shorter pause time and limit results to 3 to avoid timeouts
        results = list(search(query, num=3, pause=2.0, stop=3))
        return {"results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}

def google_image_search(query):
    """Search for images on Google and download them"""
    # First check if there are existing images
    if os.path.exists(DOWNLOADED_DIR) and os.listdir(DOWNLOADED_DIR):
        return {"status": "confirm_override", "query": query}
    
    return perform_image_search(query)

def perform_image_search(query, override=False):
    """Execute the image search and download"""
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
