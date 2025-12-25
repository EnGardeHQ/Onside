"""Time utility functions."""
from datetime import timedelta
from typing import Union

def get_time_window(timeframe: str) -> timedelta:
    """Convert timeframe string to timedelta.
    
    Args:
        timeframe: String representing time window (e.g., '1d', '7d', '30d', '1h', '6h')
        
    Returns:
        timedelta object representing the time window
        
    Raises:
        ValueError: If timeframe format is invalid
    """
    try:
        value = int(timeframe[:-1])
        unit = timeframe[-1].lower()
        
        if unit == 'd':
            return timedelta(days=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        else:
            raise ValueError(f"Invalid time unit: {unit}")
    except (IndexError, ValueError):
        raise ValueError(f"Invalid timeframe format: {timeframe}")

def format_duration(duration: Union[int, float, timedelta]) -> str:
    """Format duration in seconds to human readable string.
    
    Args:
        duration: Duration in seconds or timedelta object
        
    Returns:
        Formatted string (e.g., '2 hours 30 minutes')
    """
    if isinstance(duration, timedelta):
        seconds = int(duration.total_seconds())
    else:
        seconds = int(duration)
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not parts:  # Only show seconds if no larger units
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ' '.join(parts) if parts else '0 seconds'
