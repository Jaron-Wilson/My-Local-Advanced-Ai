"""
Package containing implementations of tool functions.
"""

# Import all functions for easy access
from .time_functions import get_current_time, get_current_date
from .search_functions import google_search, google_image_search, perform_image_search, handle_image_files
from .web_functions import read_webpage, clean_text
from .image_functions import generate_image, open_saved_image, what_is_this_image
from .file_functions import (
    open_file, list_files, download_file, move_file,
    copy_file, delete_file, rename_file, analyze_file
)
from .weather_functions import get_weather, get_weather_forecast
