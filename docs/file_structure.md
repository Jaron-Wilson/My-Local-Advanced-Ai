## Current structure
- examples (Main Directory IDK why i called it that)
 - docs/ (all md files)
 - images/
    - downloaded_images (from download image tool)
    - generated_images (From stable diffusion tool)
 - logs/ (contains .log files from assistant)
 - pdf/ (pdf's that got downloaded or needed for analyzing)
 - Scripts/ (The big boy (Contains all the scripts needed to run) {might rename to something that is more advanced})
    - lm_stuio/ (Testing out the sdk{not working rn} and test calling api from localhost)
    - tool_streaming_chatbot.py (is main running file)
    - chatbot_api_webaccess.py (is api running for localhost, so i can call via esp32's)
    - run.bat (Call for image generation) <DO NOT TOUCH>
 - static/ (Website!)
 - webui/ (as called image generation DONT TOUCH!) <DO NOT TOUCH>
 - .env (Dont mess with! Mine!) <DO NOT TOUCH>
 - README.md (what i talk about)
 - requirements.txt (Bruh you know)
 - run_api.py (file that i used <- see how its past tense) <DO NOT TOUCH>
 - tool-streaming-chatbot_tools.py (First script i made did not want to touch) <DO NOT TOUCH>

## Running cleanup.bat or cleanup_old_files.py
 - If you run this after I have updated the code base, you will get 2 options
 - if you messed up and it cleared the files into the .old directory, 
 - then press 2 to restore them.
 - ALL OLDER FILES ARE IN .old, I remade files that needed to be fixed/redone based off new structure
## New Structure
- examples/
  - docs/ (all md files)
  - images/
    - downloaded_images/ (from download image tool)
    - generated_images/ (From stable diffusion tool)
  - logs/ (contains .log files from assistant)
  - pdf/ (pdf's that got downloaded or needed for analyzing)
  - Scripts/
    - lm_stuio/ (Testing out the sdk and test calling api from localhost)
    - tools/ (Package containing all tool definitions and functions)
      - __init__.py (Makes 'tools' a proper Python package)
      - config.py (Constants and configuration for all tools)
      - time_tools.py (Time and date related tools)
      - search_tools.py (Web search related tools)
      - file_tools.py (File system operations)
      - image_tools.py (Image generation and manipulation)
      - weather_tools.py (Weather information tools)
      - web_tools.py (Web content extraction tools)
    - functions/ (Implementations of tool functions)
      - __init__.py (Package initialization)
      - time_functions.py (Time and date function implementations)
      - search_functions.py (Web search function implementations)
      - file_functions.py (File system function implementations)
      - image_functions.py (Image related function implementations)
      - weather_functions.py (Weather data functions)
      - web_functions.py (Web content extraction functions)
    - chatbot.py (Main chatbot implementation - refactored from tool_streaming_chatbot.py)
    - chatbot_api_webaccess.py (API running for localhost, for ESP32 access)
    - run.bat (Call for image generation) <DO NOT TOUCH>
  - static/ (Website!)
  - webui/ (as called image generation DONT TOUCH!) <DO NOT TOUCH>
  - .env (Dont mess with! Mine!) <DO NOT TOUCH>
  - README.md (what i talk about)
  - requirements.txt (Bruh you know)
  - run_api.py (file that i used <- see how its past tense) <DO NOT TOUCH>
  - tool-streaming-chatbot_tools.py (First script i made did not want to touch) <DO NOT TOUCH>

## Refactoring Purpose
The refactoring separates the 2000+ line tool_streaming_chatbot.py file into logically organized modules:

- **Tools**: The tool definitions (JSON structures attached to the chatbot)
- **Functions**: The implementations that the tools call
- **Main Chatbot**: The core chatbot logic that uses the tools

This organization makes the codebase:
1. More maintainable - changes to specific tools won't affect the whole system
2. More understandable - developers can find relevant code without searching through a monolithic file
3. More extensible - new tools can be added in the appropriate module without touching other parts
