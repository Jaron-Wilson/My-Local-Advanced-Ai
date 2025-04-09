"""
Configuration constants for all tools
"""
import os

# Create directories for images
IMAGE_DIR = "./images"
GENERATED_DIR = os.path.join(IMAGE_DIR, "generated_images")
DOWNLOADED_DIR = os.path.join(IMAGE_DIR, "downloaded_images")

# Ensure directories exist
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(DOWNLOADED_DIR, exist_ok=True)
