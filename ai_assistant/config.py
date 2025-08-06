import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
MODEL = os.getenv("MODEL", "qwen2.5-7b-instruct-1m")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY = os.getenv("API_KEY", "lm-studio")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Image directories
IMAGE_DIR = "./images"
GENERATED_DIR = os.path.join(IMAGE_DIR, "generated_images")
DOWNLOADED_DIR = os.path.join(IMAGE_DIR, "downloaded_images")

os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(DOWNLOADED_DIR, exist_ok=True)
