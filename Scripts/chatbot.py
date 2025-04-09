"""
Main chatbot implementation that utilizes all the tools
"""
import json
import sys
import os
from openai import OpenAI
import time
from dotenv import load_dotenv

# Add the current directory to Python path to help imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import tool definitions
from tools import ALL_TOOLS

# Import tool functions
from functions import (
    get_current_time, get_current_date,
    google_search, google_image_search, perform_image_search,
    read_webpage,
    generate_image, open_saved_image, what_is_this_image,
    open_file, list_files, download_file, move_file,
    copy_file, delete_file, rename_file, analyze_file,
    get_weather, get_weather_forecast
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with LM Studio endpoint
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
MODEL = "qwen2.5-7b-instruct-1m"  # Default model

# Create a mapping of tool names to their corresponding functions
TOOL_FUNCTION_MAP = {
    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
    "google_search": google_search,
    "google_image_search": google_image_search,
    "read_webpage": lambda args: read_webpage(args.get("url")),
    "generate_image": lambda args: generate_image(
        prompt=args.get("prompt"),
        negative_prompt=args.get("negative_prompt", ""),
        steps=args.get("steps", 20),
        width=args.get("width", 512),
        height=args.get("height", 512)
    ),
    "open_saved_image": lambda args: open_saved_image(args.get("filename")),
    "open_file": lambda args: open_file(args.get("filepath")),
    "list_files": lambda args: list_files(
        path=args.get("path"),
        pattern=args.get("pattern", "*")
    ),
    "get_weather": lambda args: get_weather(args.get("location")),
    "get_weather_forecast": lambda args: get_weather_forecast(args.get("location")),
    "download_file": lambda args: download_file(
        url=args.get("url"),
        save_path=args.get("save_path")
    ),
    "move_file": lambda args: move_file(
        source=args.get("source"),
        destination=args.get("destination")
    ),
    "copy_file": lambda args: copy_file(
        source=args.get("source"),
        destination=args.get("destination")
    ),
    "delete_file": lambda args: delete_file(args.get("path")),
    "rename_file": lambda args: rename_file(
        path=args.get("path"),
        new_name=args.get("new_name")
    ),
    "analyze_file": lambda args: analyze_file(args.get("file_path")),
    "what_is_this_image": lambda args: what_is_this_image(args.get("image_path"))
}

def process_stream(stream, add_assistant_label=True):
    """Handle streaming responses from the API"""
    collected_text = ""
    tool_calls = []
    first_chunk = True
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Handle regular text output
        if delta.content:
            if first_chunk:
                print()
                if add_assistant_label:
                    print("Assistant:", end=" ", flush=True)
                first_chunk = False
            print(delta.content, end="", flush=True)
            collected_text += delta.content
            
        # Handle tool calls
        elif delta.tool_calls:
            for tc in delta.tool_calls:
                if len(tool_calls) <= tc.index:
                    tool_calls.append({
                        "id": "", 
                        "type": "function",
                        "function": {"name": "", "arguments": ""}
                    })
                    
                tool_calls[tc.index] = {
                    "id": (tool_calls[tc.index]["id"] + (tc.id or "")),
                    "type": "function",
                    "function": {
                        "name": (tool_calls[tc.index]["function"]["name"] + (tc.function.name or "")),
                        "arguments": (tool_calls[tc.index]["function"]["arguments"] + (tc.function.arguments or ""))
                    }
                }
                
    return collected_text, tool_calls

def chat_loop():
    """Main chat loop that handles user input and chatbot responses"""
    messages = [
        {"role": "system", "content": "You are an advanced AI assistant with access to tools including web search, image generation, and file management. Help users accomplish tasks by utilizing these tools effectively. Be concise but helpful in your responses."}
    ]
    pending_image_query = None
    
    print("Assistant: Hi! I am an AI agent empowered with various tools including web browsing and image generation. (Type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == "quit":
            break
            
        # Handle pending image override confirmation
        if pending_image_query:
            if user_input.lower() in ['yes', 'y']:
                result = perform_image_search(pending_image_query["query"], override=True)
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": pending_image_query["tool_call_id"]
                })
            elif user_input.lower() in ['no', 'n']:
                result = perform_image_search(pending_image_query["query"], override=False)
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": pending_image_query["tool_call_id"]
                })
            pending_image_query = None
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        # Get initial response
        response_text, tool_calls = process_stream(
            client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=ALL_TOOLS,
                stream=True,
                temperature=0.2
            )
        )
        
        if not tool_calls:
            print()
            
        text_in_first_response = len(response_text) > 0
        if text_in_first_response:
            messages.append({"role": "assistant", "content": response_text})
            
        # Handle tool calls if any
        if tool_calls:
            tool_name = tool_calls[0]["function"]["name"]
            print()
            if not text_in_first_response:
                print("Assistant:", end=" ", flush=True)
            print(f"**Calling Tool: {tool_name}**")
            
            messages.append({"role": "assistant", "tool_calls": tool_calls})
            
            # Execute tool calls using the function map instead of if-elif chain
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                
                try:
                    query_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON arguments for {function_name}.")
                    continue
                
                # Special case for google_image_search that needs confirmation
                if function_name == "google_image_search":
                    result = google_image_search(query_args.get("query", ""))
                    if result.get("status") == "confirm_override":
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)")
                        pending_image_query = {
                            "query": result["query"],
                            "tool_call_id": tool_call["id"]
                        }
                        continue
                # For all other functions, use the function map
                elif function_name in TOOL_FUNCTION_MAP:
                    result = TOOL_FUNCTION_MAP[function_name](query_args)
                else:
                    result = {"error": f"Unknown tool function: {function_name}"}
                
                # Add the tool result to the messages
                messages.append({
                    "role": "tool", 
                    "content": str(result), 
                    "tool_call_id": tool_call["id"]
                })
                
            # If we didn't have a pending image query, get final response after tool execution
            if not pending_image_query:
                final_response, _ = process_stream(
                    client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        stream=True
                    ),
                    add_assistant_label=False
                )
                
                if final_response:
                    print()
                    messages.append({"role": "assistant", "content": final_response})

if __name__ == "__main__":
   chat_loop()
