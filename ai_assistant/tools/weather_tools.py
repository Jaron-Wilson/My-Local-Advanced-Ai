import os
import requests

# Tool definitions
GET_WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            "required": ["location"]
        }
    }
}

GET_WEATHER_FORECAST_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            "required": ["location"]
        }
    }
}

# Tool implementations
def get_weather(location):
    """Fetch current weather for a given location using WeatherAPI"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {"error": "API key for WeatherAPI is missing. Please check your .env file."}

        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": f"Failed to fetch weather data. Status code: {response.status_code}"}

        data = response.json()
        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"]
        }
    except Exception as e:
        return {"error": f"An error occurred while fetching weather data: {str(e)}"}

def get_weather_forecast(location):
    """Fetch weather forecast for a given location using WeatherAPI"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return {"error": "API key for WeatherAPI is missing. Please check your .env file."}

        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": f"Failed to fetch weather forecast. Status code: {response.status_code}"}

        data = response.json()
        forecast = []
        for day in data["forecast"]["forecastday"]:
            forecast.append({
                "date": day["date"],
                "max_temp_c": day["day"]["maxtemp_c"],
                "min_temp_c": day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"]
            })

        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "forecast": forecast
        }
    except Exception as e:
        return {"error": f"An error occurred while fetching weather forecast: {str(e)}"}

# Export tools
tools = [GET_WEATHER_TOOL, GET_WEATHER_FORECAST_TOOL]
tool_functions = {
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast,
}
