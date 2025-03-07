from openai import OpenAI
import time
from googlesearch import search
from icrawler.builtin import GoogleImageCrawler
import os
import json
import requests
from bs4 import BeautifulSoup
import re

IMAGE_DIR = "./images"

client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
MODEL = "lmstudio-community/qwen2.5-7b-instruct"

TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Get the current time, only if asked",
        "parameters": {"type": "object", "properties": {}}
    }
}

DATE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_date",
        "description": "Get the current date, only if asked",
        "parameters": {"type": "object", "properties": {}}
    }
}

GOOGLE_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "google_search",
        "description": "Perform a Google search and return the top result.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to look up."}
            },
            "required": ["query"]
        }
    }
}

GOOGLE_IMAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "google_image_search",
        "description": "Search for an image on Google and download it.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The image search term."}
            },
            "required": ["query"]
        }
    }
}

WEBPAGE_READ_TOOL = {
    "type": "function",
    "function": {
        "name": "read_webpage",
        "description": "Read and summarize the content of a webpage",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the webpage to read"}
            },
            "required": ["url"]
        }
    }
}

def get_current_time():
    return {"time": time.strftime("%H:%M:%S")}

def get_current_date():
    return {"date": time.strftime("%Y-%m-%d")}

def google_search(query):
    try:
        # Use a shorter pause time (2 seconds) and limit results to 3 to avoid timeouts
        results = list(search(query, num=3, pause=2.0, stop=3))
        return {"results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}

def handle_image_files(query, override=False):
    """Helper function to manage image files"""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    
    if override and os.path.exists(IMAGE_DIR):
        # Remove existing images if override is True
        for file in os.listdir(IMAGE_DIR):
            os.remove(os.path.join(IMAGE_DIR, file))
    
    base_path = os.path.join(IMAGE_DIR, query.replace(" ", "_"))
    suffix = 1
    while os.path.exists(f"{base_path}_{suffix}"):
        suffix += 1
    
    return f"{base_path}_{suffix}"

def google_image_search(query):
    # First check if there are existing images
    if os.path.exists(IMAGE_DIR) and os.listdir(IMAGE_DIR):
        return {"status": "confirm_override", "query": query}
    
    return perform_image_search(query)

def perform_image_search(query, override=False):
    save_dir = handle_image_files(query, override)
    
    crawler = GoogleImageCrawler(storage={"root_dir": os.path.dirname(save_dir)})
    crawler.crawl(keyword=query, max_num=3)
    
    # Rename downloaded files to our desired format
    files = os.listdir(os.path.dirname(save_dir))
    if files:
        for i, file in enumerate(files, 1):
            old_path = os.path.join(os.path.dirname(save_dir), file)
            new_path = f"{save_dir}_{i}{os.path.splitext(file)[1]}"
            os.rename(old_path, new_path)
        return {"image_paths": [f"{save_dir}_{1}"]}
    return {"error": "No images found"}

def clean_text(text):
    """Clean extracted text by removing extra whitespace and unwanted characters"""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
    return text.strip()

def read_webpage(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract main content (adjust selectors based on common website structures)
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3'])
            content = '\n'.join(p.get_text() for p in paragraphs)
        else:
            content = soup.get_text()
        
        cleaned_content = clean_text(content)
        return {"content": cleaned_content[:2000]}  # Limit content length
    except Exception as e:
        return {"error": f"Failed to read webpage: {str(e)}"}

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
                        "id": "", "type": "function",
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
    messages = []
    pending_image_query = None
    print("Assistant: Hi! I am an AI agent empowered with various tools including web browsing. (Type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip().lower()
        if user_input == "quit":
            break

        # Handle pending image override confirmation
        if pending_image_query:
            if user_input in ['yes', 'y']:
                result = perform_image_search(pending_image_query["query"], override=True)
                messages.append({"role": "tool", "content": str(result), "tool_call_id": pending_image_query["tool_call_id"]})
            elif user_input in ['no', 'n']:
                result = perform_image_search(pending_image_query["query"], override=False)
                messages.append({"role": "tool", "content": str(result), "tool_call_id": pending_image_query["tool_call_id"]})
            pending_image_query = None
            continue

        messages.append({"role": "user", "content": user_input})

        # Get initial response
        response_text, tool_calls = process_stream(
            client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL],
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

            # Execute tool calls
            for tool_call in tool_calls:
                try:
                    query_args = json.loads(tool_call["function"]["arguments"])
                    query = query_args.get("query", "")
                except json.JSONDecodeError:
                    print("Error: Invalid JSON arguments.")
                    continue

                if tool_call["function"]["name"] == "get_current_time":
                    result = get_current_time()
                elif tool_call["function"]["name"] == "get_current_date":
                    result = get_current_date()
                elif tool_call["function"]["name"] == "google_search":
                    result = google_search(query)
                elif tool_call["function"]["name"] == "google_image_search":
                    result = google_image_search(query)
                    if result.get("status") == "confirm_override":
                        print("\nAssistant: There are existing images. Would you like to override them? (yes/no)")
                        pending_image_query = {
                            "query": result["query"],
                            "tool_call_id": tool_call["id"]
                        }
                        continue
                elif tool_call["function"]["name"] == "read_webpage":
                    result = read_webpage(query_args["url"])
                
                messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]})

            # Get final response after tool execution
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
