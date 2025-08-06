import time
import psutil

# Tool definitions
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

SYSTEM_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_system_info",
        "description": "Get system information, such as CPU and memory usage.",
        "parameters": {"type": "object", "properties": {}}
    }
}

# Tool implementations
def get_current_time():
    return {"time": time.strftime("%H:%M:%S")}

def get_current_date():
    return {"date": time.strftime("%Y-%m-%d")}

def get_system_info():
    """Get system information (CPU and memory usage)."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()

    return {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory_info.percent,
        "available_memory_gb": round(memory_info.available / (1024**3), 2),
        "total_memory_gb": round(memory_info.total / (1024**3), 2),
    }

# Export tools
tools = [TIME_TOOL, DATE_TOOL, SYSTEM_INFO_TOOL]
tool_functions = {
    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
    "get_system_info": get_system_info,
}
