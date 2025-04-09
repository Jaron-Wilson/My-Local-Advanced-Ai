from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from markdown import markdown
import uvicorn
import asyncio
import os
from dotenv import load_dotenv
import sys
import pathlib
import json

# Fix import by using absolute import instead of relative
import tool_streaming_chatbot
from tool_streaming_chatbot import (
    get_current_time, get_current_date, google_search,
    google_image_search, read_webpage,
    get_weather, get_weather_forecast, generate_image,
    open_saved_image, open_file, list_files, download_file, 
    move_file, copy_file, delete_file, rename_file, analyze_file,
    what_is_this_image, perform_image_search,
    TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL,
    WEBPAGE_READ_TOOL, GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL,
    TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, OPEN_FILE_TOOL, LIST_FILES_TOOL, 
    DOWNLOAD_FILE_TOOL, MOVE_FILE_TOOL, COPY_FILE_TOOL, DELETE_FILE_TOOL, 
    RENAME_FILE_TOOL, ANALYZE_FILE_TOOL, WHAT_IS_THIS_IMAGE_TOOL,
    process_stream
)

# Import OpenAI client from tool_streaming_chatbot
client = tool_streaming_chatbot.client
MODEL = tool_streaming_chatbot.MODEL

# Import constants separately to avoid any potential issues
GENERATED_DIR = tool_streaming_chatbot.GENERATED_DIR
DOWNLOADED_DIR = tool_streaming_chatbot.DOWNLOADED_DIR

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Chatbot API",
    version="1.0.0",
    description="API for accessing chatbot tools and functionality"
)

# Mount static files directory
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main HTML interface"""
    index_path = os.path.join(static_path, "index.html")
    with open(index_path, 'r') as f:
        return f.read()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data models
class ChatMessage(BaseModel):
    content: str
    markdown: Optional[bool] = True


class ToolCall(BaseModel):
    tool: str
    args: Dict[str, Any]


class ImageGeneration(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    steps: Optional[int] = 20
    width: Optional[int] = 512
    height: Optional[int] = 512


class WeatherRequest(BaseModel):
    location: str


class FileListRequest(BaseModel):
    path: str
    pattern: Optional[str] = "*"


class FileOperationRequest(BaseModel):
    source: str
    destination: str


class FilePathRequest(BaseModel):
    path: str


class FileDownloadRequest(BaseModel):
    url: str
    save_path: str


# New data models for rename and image analysis
class FileRenameRequest(BaseModel):
    path: str
    new_name: str


class ImageAnalysisRequest(BaseModel):
    image_path: str


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    stream: Optional[bool] = True
    temperature: Optional[float] = 0.2


# API endpoints
@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        # Create a more complete chat system
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to various tools."},
            {"role": "user", "content": message.content}
        ]

        # Get a response from the model
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2
        )

        # Return the response text
        response_text = response.choices[0].message.content
        if message.markdown:
            response_text = markdown(response_text)

        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add a more advanced endpoint for multi-turn conversations
@app.post("/conversation")
async def conversation(messages: List[Dict[str, str]] = Body(...)):
    try:
        # Check message content for image generation request
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                if any(phrase in user_message for phrase in [
                    "generate image", "create image", "draw", "make an image",
                    "generate a picture", "create a picture", "show me an image",
                    "visualize", "generate an image", "create an illustration"
                ]):
                    # Extract the prompt from the message
                    prompt_parts = []
                    for phrase in ["of:", "of", "showing", "that shows", "with", "depicting"]:
                        if phrase in user_message:
                            prompt_parts = user_message.split(phrase, 1)
                            break

                    if len(prompt_parts) > 1:
                        prompt = prompt_parts[1].strip()
                        # Generate the image
                        result = generate_image(prompt=prompt)
                        # Create response with image paths
                        if "images" in result and result["images"]:
                            image_paths = [path.replace('\\', '/') for path in result["images"]]
                            images_html = "I've generated these images:<br>"
                            for path in image_paths:
                                images_html += f'<img src="/image/{path}" style="max-width:100%;margin:10px 0;"><br>'

                            return {
                                "response": images_html,
                                "messages": messages + [{"role": "assistant",
                                                         "content": f"I've generated images based on your request: '{prompt}'"}]
                            }

        # If not an image generation request, proceed with regular response
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL,
                   GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL,
                   # Use updated weather tools
                   GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL,
                   TEXT_TO_IMAGE_TOOL,
                   # Added OPEN_IMAGE_TOOL
                   OPEN_IMAGE_TOOL,
                   MOVE_FILE_TOOL,
                   DELETE_FILE_TOOL, DOWNLOAD_FILE_TOOL,
                   # Add existing/new tools
                   OPEN_FILE_TOOL, ANALYZE_FILE_TOOL,
                   # Add rename and image analysis tools
                   RENAME_FILE_TOOL, WHAT_IS_THIS_IMAGE_TOOL],
            temperature=0.2
        )

        response_text = response.choices[0].message.content
        return {
            "response": response_text,
            "messages": messages + [{"role": "assistant", "content": response_text}]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool")
async def call_tool(tool_call: ToolCall):
    try:
        result = None
        tool_map = {
            "get_time": get_current_time,
            "get_date": get_current_date,
            "search": lambda q: google_search(q),
            "generate_image": generate_image,
            # Use updated weather functions
            "get_weather": get_weather,
            "get_weather_forecast": get_weather_forecast,
            "read_webpage": read_webpage,
            # Add new tools
            "open_file": open_file,
            "analyze_file": analyze_file,
            # Add rename and image analysis
            "rename_file": rename_file,
            "what_is_this_image": what_is_this_image,
            # Add missing tool mappings
            "google_image_search": google_image_search,
            "open_saved_image": open_saved_image,
            "list_files": list_files,
            "download_file": download_file,
            "move_file": move_file,
            "delete_file": delete_file,
        }

        if tool_call.tool in tool_map:
            if tool_call.args:
                result = tool_map[tool_call.tool](**tool_call.args)
            else:
                result = tool_map[tool_call.tool]()

        if result is None:
            raise HTTPException(status_code=400, detail="Unknown tool or invalid args")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images")
async def list_images():
    return list_available_images()


@app.get("/image/{image_path:path}")
async def serve_image(image_path: str):
    try:
        # Check both directories
        if os.path.exists(os.path.join(GENERATED_DIR, image_path)):
            return FileResponse(os.path.join(GENERATED_DIR, image_path))
        elif os.path.exists(os.path.join(DOWNLOADED_DIR, image_path)):
            return FileResponse(os.path.join(DOWNLOADED_DIR, image_path))
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate(params: ImageGeneration):
    try:
        result = generate_image(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            steps=params.steps,
            width=params.width,
            height=params.height
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/weather/current")
async def weather_current(req: WeatherRequest):
    try:
        # Use the updated get_weather function
        return get_weather(req.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/weather/forecast")
async def weather_forecast(req: WeatherRequest):
    try:
        # Use the updated get_weather_forecast function
        return get_weather_forecast(req.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/list")
async def api_list_files(req: FileListRequest):
    try:
        return list_files(req.path, req.pattern)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/move")
async def api_move_file(req: FileOperationRequest):
    try:
        return move_file(req.source, req.destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/delete")
async def api_delete_file(req: FilePathRequest):
    try:
        return delete_file(req.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/download")
async def api_download_file(req: FileDownloadRequest):
    try:
        return download_file(req.url, req.save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add new file system endpoint for renaming
@app.post("/files/rename")
async def api_rename_file(req: FileRenameRequest):
    try:
        return rename_file(req.path, req.new_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail.str(e))


# Add new image analysis endpoint
@app.post("/images/analyze")
async def api_analyze_image(req: ImageAnalysisRequest):
    try:
        return what_is_this_image(req.image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/open")
async def api_open_file(req: FilePathRequest):
    try:
        return open_file(req.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Process a chat request and return the response"""
    try:
        if request.stream:
            return StreamingResponse(
                stream_chat_response(request.messages, request.temperature),
                media_type="text/event-stream"
            )
        else:
            # Non-streaming response
            response, tool_calls = process_stream(
                client.chat.completions.create(
                    model=MODEL,
                    messages=request.messages,
                    tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL,
                           GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL,
                           TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, OPEN_FILE_TOOL, LIST_FILES_TOOL, DOWNLOAD_FILE_TOOL,
                           MOVE_FILE_TOOL, COPY_FILE_TOOL, DELETE_FILE_TOOL, RENAME_FILE_TOOL, ANALYZE_FILE_TOOL, 
                           WHAT_IS_THIS_IMAGE_TOOL],
                    stream=True,
                    temperature=request.temperature
                )
            )
            return {"response": response, "tool_calls": tool_calls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_chat_response(messages, temperature=0.2):
    """Stream the chat response back to the client"""
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL,
                   GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL,
                   TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, OPEN_FILE_TOOL, LIST_FILES_TOOL, DOWNLOAD_FILE_TOOL,
                   MOVE_FILE_TOOL, COPY_FILE_TOOL, DELETE_FILE_TOOL, RENAME_FILE_TOOL, ANALYZE_FILE_TOOL, 
                   WHAT_IS_THIS_IMAGE_TOOL],
            stream=True,
            temperature=temperature
        )
        
        for chunk in stream:
            if hasattr(chunk.choices[0], 'delta'):
                delta = chunk.choices[0].delta
                
                # Format the response for SSE
                response_data = {}
                
                if delta.content:
                    response_data["content"] = delta.content
                
                elif delta.tool_calls:
                    tc_data = []
                    for tc in delta.tool_calls:
                        tc_info = {
                            "index": tc.index
                        }
                        if tc.id:
                            tc_info["id"] = tc.id
                        if tc.function and tc.function.name:
                            tc_info["function"] = {"name": tc.function.name}
                        if tc.function and tc.function.arguments:
                            if "function" not in tc_info:
                                tc_info["function"] = {}
                            tc_info["function"]["arguments"] = tc.function.arguments
                        
                        tc_data.append(tc_info)
                    
                    response_data["tool_calls"] = tc_data
                
                if response_data:
                    yield f"data: {json.dumps(response_data)}\n\n"
                
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_msg = {"error": str(e)}
        yield f"data: {json.dumps(error_msg)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/api/tool/execute")
async def execute_tool(tool_data: ToolCall):
    """Execute a specific tool with the provided arguments"""
    try:
        tool_name = tool_data.tool
        args = tool_data.args
        
        # Route to the appropriate tool handler
        if tool_name == "get_current_time":
            result = get_current_time()
        elif tool_name == "get_current_date":
            result = get_current_date()
        elif tool_name == "google_search":
            result = google_search(args.get("query", ""))
        elif tool_name == "google_image_search":
            result = google_image_search(args.get("query", ""))
        elif tool_name == "read_webpage":
            result = read_webpage(args.get("url", ""))
        elif tool_name == "get_weather":
            result = get_weather(args.get("location", ""))
        elif tool_name == "get_weather_forecast":
            result = get_weather_forecast(args.get("location", ""))
        elif tool_name == "generate_image":
            result = generate_image(args.get("prompt", ""), args.get("negative_prompt", ""), 
                                  args.get("steps", 20), args.get("width", 512), args.get("height", 512))
        elif tool_name == "open_saved_image":
            result = open_saved_image(args.get("filename", ""))
        elif tool_name == "open_file":
            result = open_file(args.get("filepath", ""))
        elif tool_name == "list_files":
            result = list_files(args.get("directory", ""))
        elif tool_name == "download_file":
            result = download_file(args.get("url", ""), args.get("filename", ""))
        elif tool_name == "move_file":
            result = move_file(args.get("source", ""), args.get("destination", ""))
        elif tool_name == "copy_file":
            result = copy_file(args.get("source", ""), args.get("destination", ""))
        elif tool_name == "delete_file":
            result = delete_file(args.get("filepath", ""))
        elif tool_name == "rename_file":
            result = rename_file(args.get("old_path", ""), args.get("new_name", ""))
        elif tool_name == "analyze_file":
            result = analyze_file(args.get("filepath", ""))
        elif tool_name == "what_is_this_image":
            result = what_is_this_image(args.get("image_path", ""))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
            
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image-search-override")
async def image_search_override(data: dict = Body(...)):
    """Handle image search override confirmation"""
    try:
        query = data.get("query", "")
        override = data.get("override", False)
        
        result = perform_image_search(query, override)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
