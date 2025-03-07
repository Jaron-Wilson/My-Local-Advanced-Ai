import sys
import os

# Add the Scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scripts'))

# Import and run the API
from Scripts.chatbot_api_webaccess import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
