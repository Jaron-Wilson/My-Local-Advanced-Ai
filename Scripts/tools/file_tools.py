"""
File system operation tools
"""

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
