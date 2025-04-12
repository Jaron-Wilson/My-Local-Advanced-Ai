"""
Package containing all tool definitions for the chatbot.
Tools are defined as JSON structures that can be attached to the chatbot.
"""

# Import all tools from the respective modules
from .time_tools import TIME_TOOL, DATE_TOOL
from .search_tools import GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, PERFORM_IMAGE_SEARCH
from .web_tools import WEBPAGE_READ_TOOL
from .image_tools import TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, WHAT_IS_THIS_IMAGE_TOOL
from .file_tools import (OPEN_FILE_TOOL, LIST_FILES_TOOL, DOWNLOAD_FILE_TOOL,
                         MOVE_FILE_TOOL, COPY_FILE_TOOL, DELETE_FILE_TOOL,
                         RENAME_FILE_TOOL, ANALYZE_FILE_TOOL)
from .weather_tools import GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL

# Dictionary of all available tools for easy access
ALL_TOOLS = [
    # Time tools
    TIME_TOOL,
    DATE_TOOL,

    # Search tools
    GOOGLE_SEARCH_TOOL,
    GOOGLE_IMAGE_TOOL,
    PERFORM_IMAGE_SEARCH,

    # Web tools
    WEBPAGE_READ_TOOL,

    # Image tools
    TEXT_TO_IMAGE_TOOL,
    OPEN_IMAGE_TOOL,
    WHAT_IS_THIS_IMAGE_TOOL,

    # File tools
    OPEN_FILE_TOOL,
    LIST_FILES_TOOL,
    DOWNLOAD_FILE_TOOL,
    MOVE_FILE_TOOL,
    COPY_FILE_TOOL,
    DELETE_FILE_TOOL,
    RENAME_FILE_TOOL,
    # ANALYZEING FILES
    ANALYZE_FILE_TOOL,

    # Weather tools
    GET_WEATHER_TOOL,
    GET_WEATHER_FORECAST_TOOL,
]
