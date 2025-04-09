"""
Time and date related function implementations
"""
import time

def get_current_time():
    """Return the current time in HH:MM:SS format"""
    return {"time": time.strftime("%H:%M:%S")}

def get_current_date():
    """Return the current date in YYYY-MM-DD format"""
    return {"date": time.strftime("%Y-%m-%d")}
