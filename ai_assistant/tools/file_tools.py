import os
import platform
import subprocess
import shutil
import glob
import time

# Tool definitions
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


# Export tools
tools = [
    OPEN_FILE_TOOL,
    LIST_FILES_TOOL,
    MOVE_FILE_TOOL,
    COPY_FILE_TOOL,
    DELETE_FILE_TOOL,
    RENAME_FILE_TOOL,
    ANALYZE_FILE_TOOL,
]
tool_functions = {
    "open_file": open_file,
    "list_files": list_files,
    "move_file": move_file,
    "copy_file": copy_file,
    "delete_file": delete_file,
    "rename_file": rename_file,
    "analyze_file": analyze_file,
}
