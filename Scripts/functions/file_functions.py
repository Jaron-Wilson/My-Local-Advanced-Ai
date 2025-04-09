"""
File system operations function implementations
"""
import os
import time
import glob
import platform
import subprocess
import shutil

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

def download_file(url, save_path):
    """Download a file from a URL to the specified local path"""
    try:
        import requests
        
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
    """Move a file from one location to another"""
    try:
        shutil.move(source, destination)
        return {"status": "success", "message": f"Moved file from {source} to {destination}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move file: {str(e)}"}

def copy_file(source, destination):
    """Copy a file from one location to another"""
    try:
        shutil.copy(source, destination)
        return {"status": "success", "message": f"Copied file from {source} to {destination}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy file: {str(e)}"}

def delete_file(path):
    """Delete a file from the file system"""
    try:
        os.remove(path)
        return {"status": "success", "message": f"Deleted file: {path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete file: {str(e)}"}

def rename_file(path, new_name):
    """Rename a file to a new name"""
    try:
        directory = os.path.dirname(path)
        new_path = os.path.join(directory, new_name)
        os.rename(path, new_path)
        return {"status": "success", "message": f"Renamed file to {new_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rename file: {str(e)}"}

def analyze_file(file_path):
    """Analyze the content of a specified file"""
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": f"Failed to analyze file: {str(e)}"}
