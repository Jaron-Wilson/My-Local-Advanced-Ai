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

# Fix import by using absolute import instead of relative
import tool_streaming_chatbot
from tool_streaming_chatbot import (
    get_current_time, get_current_date, google_search,
    google_image_search, read_webpage, background_check,
    listen_voice, speak_text, analyze_pdf, summarize_youtube,
    get_weather_current, get_weather_forcast, generate_image, 
    list_available_images, open_saved_image, perform_image_search,
    TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, GOOGLE_IMAGE_TOOL,
    WEBPAGE_READ_TOOL, BACKGROUND_CHECK_TOOL, VOICE_TOOL, PDF_TOOL, 
    YOUTUBE_TOOL, WEATHER_CURRENT_TOOL, WEATHER_FORCAST_TOOL,
    TEXT_TO_IMAGE_TOOL, OPEN_IMAGE_TOOL, SPEAK_TOOL,
    list_files, move_file, copy_file, delete_file, download_file,
    FILE_LIST_TOOL, FILE_MOVE_TOOL, FILE_COPY_TOOL, FILE_DELETE_TOOL, FILE_DOWNLOAD_TOOL,
    # Add tools
    search_files, open_file, analyze_file, list_available_models, select_model,
    FILE_SEARCH_TOOL, OPEN_FILE_TOOL, FILE_ANALYZE_TOOL, LIST_MODELS_TOOL, SELECT_MODEL_TOOL,
    # Add model management tools
    load_model, unload_model, LOAD_MODEL_TOOL, UNLOAD_MODEL_TOOL,
    # Add new model checking function
    check_loaded_models
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

# New data models
class FileSearchRequest(BaseModel):
    pattern: str
    location: Optional[str] = ""

class FileAnalyzeRequest(BaseModel):
    filepath: str
    analysis_type: Optional[str] = "auto"

class ModelSelectionRequest(BaseModel):
    task_type: str

# New model loading request
class ModelLoadRequest(BaseModel):
    model_id: str

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
                                "messages": messages + [{"role": "assistant", "content": f"I've generated images based on your request: '{prompt}'"}]
                            }
        
        # If not an image generation request, proceed with regular response
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[TIME_TOOL, DATE_TOOL, GOOGLE_SEARCH_TOOL, 
                  GOOGLE_IMAGE_TOOL, WEBPAGE_READ_TOOL, BACKGROUND_CHECK_TOOL,
                  VOICE_TOOL, PDF_TOOL, YOUTUBE_TOOL, WEATHER_CURRENT_TOOL,
                  TEXT_TO_IMAGE_TOOL, SPEAK_TOOL, WEATHER_FORCAST_TOOL,
                  FILE_LIST_TOOL, FILE_MOVE_TOOL, FILE_COPY_TOOL, 
                  FILE_DELETE_TOOL, FILE_DOWNLOAD_TOOL,
                  # Add new tools
                  FILE_SEARCH_TOOL, OPEN_FILE_TOOL, FILE_ANALYZE_TOOL,
                  LIST_MODELS_TOOL, SELECT_MODEL_TOOL],
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
            "weather_current": get_weather_current,
            "weather_forecast": get_weather_forcast,
            "speak": speak_text,
            "listen": listen_voice,
            "read_webpage": read_webpage,
            "background_check": background_check,
            "analyze_pdf": analyze_pdf,
            "youtube": summarize_youtube,
            # Add new tools
            "search_files": search_files,
            "open_file": open_file,
            "analyze_file": analyze_file,
            "list_available_models": list_available_models,
            "select_model": select_model,
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
        return get_weather_current(req.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/forecast")
async def weather_forecast(req: WeatherRequest):
    try:
        return get_weather_forcast(req.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/speak")
async def tts(text: str, background_tasks: BackgroundTasks):
    try:
        result = speak_text(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/listen")
async def stt():
    try:
        return listen_voice()
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

@app.post("/files/copy")
async def api_copy_file(req: FileOperationRequest):
    try:
        return copy_file(req.source, req.destination)
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

# Add new file system endpoints
@app.post("/files/search")
async def api_search_files(req: FileSearchRequest):
    try:
        return search_files(req.pattern, req.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/open")
async def api_open_file(req: FilePathRequest):
    try:
        return open_file(req.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/analyze")
async def api_analyze_file(req: FileAnalyzeRequest):
    try:
        return analyze_file(req.filepath, req.analysis_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add model management endpoints
@app.get("/models")
async def api_list_models():
    try:
        return list_available_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add a specific endpoint to check loaded models
@app.get("/models/loaded")
async def api_loaded_models():
    try:
        return check_loaded_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/select")
async def api_select_model(req: ModelSelectionRequest):
    try:
        return select_model(req.task_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add new endpoints for model loading/unloading
@app.post("/models/load")
async def api_load_model(req: ModelLoadRequest):
    try:
        return await load_model(req.model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail = str(e))

@app.post("/models/unload")
async def api_unload_model(req: ModelLoadRequest):
    try:
        return await unload_model(req.model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail = str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)