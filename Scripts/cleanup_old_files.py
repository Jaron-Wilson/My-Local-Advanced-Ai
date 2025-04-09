"""
Script to move old files to .old directories while preserving folder structure
"""
import os
import shutil
import sys
from pathlib import Path

# Define files that should not be moved (our new structure)
PROTECTED_FILES = [
    # New main script
    "chatbot.py",
    # New directory structure
    "tools",
    "functions",
    # This script itself
    "cleanup_old_files.py",
    # Special directories
    ".old",
    #basic files that should stay for chatbot to keep working
    "docs",
    "images",
    "logs",
    "pdf",
    "readme.md",
    "requirements.txt",
]

# Define files that should NEVER be moved regardless of location
DO_NOT_TOUCH = [
    "run.bat",  # <DO NOT TOUCH> flag from documentation
    ".env",     # <DO NOT TOUCH> flag from documentation
]

def create_old_directory(base_dir):
    """Create .old directory if it doesn't exist"""
    old_dir = os.path.join(base_dir, ".old")
    if not os.path.exists(old_dir):
        os.makedirs(old_dir)
    return old_dir

def should_move_file(file_path, base_dir):
    """Determine if the file should be moved based on our rules"""
    # Get the relative path from base directory
    rel_path = os.path.relpath(file_path, base_dir)
    
    # Check if this file is in our protected list
    filename = os.path.basename(file_path)
    if filename in DO_NOT_TOUCH:
        return False
    
    # If the file is in the Scripts directory, check against PROTECTED_FILES
    if os.path.dirname(rel_path) == "Scripts":
        basename = os.path.basename(file_path)
        if basename in PROTECTED_FILES:
            return False
    
    # Check if the file is inside a protected directory structure
    path_parts = rel_path.split(os.sep)
    if len(path_parts) > 1 and path_parts[0] == "Scripts":
        # Check if it's in a protected directory structure (e.g., Scripts/tools/ or Scripts/functions/)
        if len(path_parts) > 2 and path_parts[1] in PROTECTED_FILES:
            return False
    
    # For any other directory, if it contains .old, don't move it (prevent nested .old)
    return ".old" not in rel_path

def move_file_to_old(file_path, base_dir):
    """Move a file to the equivalent .old directory structure"""
    # Get the relative path from base directory
    rel_path = os.path.relpath(file_path, base_dir)
    
    # Create the destination path
    path_parts = rel_path.split(os.sep)
    
    # Insert .old after the first directory component
    if len(path_parts) > 1:
        old_path_parts = path_parts[0:1] + [".old"] + path_parts[1:]
    else:
        old_path_parts = [".old"] + path_parts
    
    old_path = os.path.join(base_dir, *old_path_parts)
    
    # Create the parent directory if it doesn't exist
    os.makedirs(os.path.dirname(old_path), exist_ok=True)
    
    # Move the file
    shutil.move(file_path, old_path)
    print(f"Moved: {rel_path} -> {os.path.join(*old_path_parts)}")

def process_directory(directory, base_dir):
    """Process a directory, moving files to .old structure"""
    # First, collect all files and directories to process
    items_to_process = []
    
    for root, dirs, files in os.walk(directory):
        # Skip .old directories to prevent circular moves
        if ".old" in root.split(os.sep):
            continue
            
        # Process files in this directory
        for filename in files:
            file_path = os.path.join(root, filename)
            if should_move_file(file_path, base_dir):
                items_to_process.append(file_path)
    
    # Now process all files (doing this separately helps avoid walk issues)
    for file_path in items_to_process:
        move_file_to_old(file_path, base_dir)

def main():
    """Main function to handle the cleanup process"""
    # Get the examples directory path
    examples_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Starting cleanup process in: {examples_dir}")
    
    # Create the .old directory in Scripts
    scripts_dir = os.path.join(examples_dir, "Scripts")
    create_old_directory(scripts_dir)
    
    # Process the Scripts directory
    process_directory(scripts_dir, examples_dir)
    
    print("\nCleanup complete. Old files have been moved to their respective .old directories.")
    print("Files with <DO NOT TOUCH> flags in the documentation were not moved.")

def restore_moved_files():
    """Function to restore files that may have been incorrectly moved"""
    examples_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(examples_dir, "Scripts")
    old_dir = os.path.join(scripts_dir, ".old")
    
    # Check if .old directory exists
    if not os.path.exists(old_dir):
        print("No .old directory found. Nothing to restore.")
        return
    
    # Check for tools and functions directories in .old
    tools_old_path = os.path.join(old_dir, "tools")
    functions_old_path = os.path.join(old_dir, "functions")
    
    # Define target paths for restoration
    tools_target_path = os.path.join(scripts_dir, "tools")
    functions_target_path = os.path.join(scripts_dir, "functions")
    
    # Create directories if they don't exist
    os.makedirs(tools_target_path, exist_ok=True)
    os.makedirs(functions_target_path, exist_ok=True)
    
    # Restore tools files
    if os.path.exists(tools_old_path):
        print("Restoring tools directory...")
        for root, dirs, files in os.walk(tools_old_path):
            for file in files:
                source_file = os.path.join(root, file)
                # Get relative path from tools_old_path
                rel_path = os.path.relpath(source_file, tools_old_path)
                target_file = os.path.join(tools_target_path, rel_path)
                
                # Create target directories if needed
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                print(f"Restored: {rel_path}")
    
    # Restore functions files
    if os.path.exists(functions_old_path):
        print("Restoring functions directory...")
        for root, dirs, files in os.walk(functions_old_path):
            for file in files:
                source_file = os.path.join(root, file)
                # Get relative path from functions_old_path
                rel_path = os.path.relpath(source_file, functions_old_path)
                target_file = os.path.join(functions_target_path, rel_path)
                
                # Create target directories if needed
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                print(f"Restored: {rel_path}")
    
    print("Restoration complete. Your tools and functions should now be back in place.")

if __name__ == "__main__":
    choice = input("Choose an option:\n1. Run cleanup\n2. Restore moved tools/functions\nEnter choice (1/2): ")
    
    if choice == "1":
        if input("This will move old files to .old directories. Continue? (y/n): ").lower() == 'y':
            main()
        else:
            print("Operation cancelled.")
    elif choice == "2":
        if input("This will restore your tools and functions directories. Continue? (y/n): ").lower() == 'y':
            restore_moved_files()
        else:
            print("Restoration cancelled.")
    else:
        print("Invalid choice. Please run the script again.")
