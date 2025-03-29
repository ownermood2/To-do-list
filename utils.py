import re
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from config import DEVELOPER_IDS

def is_developer(user_id: int) -> bool:
    """Check if a user is a developer"""
    return user_id in DEVELOPER_IDS

def format_task_list(tasks: List[Dict]) -> str:
    """Format a list of tasks for display"""
    if not tasks:
        return "No tasks found."
    
    formatted = "📝 *Your Tasks*:\n\n"
    
    for i, task in enumerate(tasks):
        # Add task number and text
        formatted += f"{i+1}. {task['text']}"
        
        # Add reminder info if present
        if 'reminder' in task:
            formatted += " ⏰"
        
        # Add newline
        formatted += "\n"
    
    return formatted

def parse_time(time_str: str) -> Optional[float]:
    """Parse a time string into absolute time (seconds since epoch)
    
    Formats supported:
    - Xh Ym (e.g., 1h 30m)
    - X hours Y minutes (e.g., 1 hour 30 minutes)
    - X:Y (e.g., 1:30 for 1h 30m)
    """
    # Pattern for Xh Ym format
    pattern_short = r'(?:(\d+)h)?\s*(?:(\d+)m)?'
    # Pattern for X hours Y minutes format
    pattern_long = r'(?:(\d+)\s*hours?)?\s*(?:(\d+)\s*minutes?)?'
    # Pattern for X:Y format (HH:MM)
    pattern_colon = r'(\d+):(\d+)'
    
    # Try short format
    match = re.fullmatch(pattern_short, time_str.strip())
    if match and (match.group(1) or match.group(2)):
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    # Try long format
    match = re.fullmatch(pattern_long, time_str.strip())
    if match and (match.group(1) or match.group(2)):
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    # Try colon format
    match = re.fullmatch(pattern_colon, time_str.strip())
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    return None

def get_current_time() -> float:
    """Get current time as seconds since epoch"""
    return time.time()

def format_task_details(task: Dict, include_status: bool = True) -> str:
    """Format a single task with detailed information"""
    formatted = f"*{task['text']}*\n"
    
    # Add status if requested
    if include_status:
        status = "✅ Done" if task.get('done', False) else "⏳ Pending"
        formatted += f"Status: {status}\n"
    
    # Add date added
    if 'date_added' in task:
        try:
            date_added = datetime.fromisoformat(task['date_added']).strftime('%Y-%m-%d %H:%M')
            formatted += f"Added: {date_added}\n"
        except (ValueError, TypeError):
            pass
    
    # Add due date if present
    if 'due_date' in task:
        try:
            due_date = datetime.fromisoformat(task['due_date']).strftime('%Y-%m-%d %H:%M')
            formatted += f"Due: {due_date}\n"
        except (ValueError, TypeError):
            pass
    
    # Add reminder if present
    if 'reminder' in task:
        try:
            reminder_time = datetime.fromtimestamp(task['reminder']).strftime('%Y-%m-%d %H:%M')
            formatted += f"Reminder: {reminder_time}\n"
        except (ValueError, TypeError, OSError):
            pass
    
    return formatted.strip()
