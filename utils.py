import re
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from config import DEVELOPER_IDS

logger = logging.getLogger(__name__)

def is_developer(user_id: int) -> bool:
    """Check if a user is a developer"""
    return user_id in DEVELOPER_IDS

def add_developer(user_id: int) -> bool:
    """Add a user to the list of developers by updating the environment variable
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add to in-memory list first
        if user_id not in DEVELOPER_IDS:
            DEVELOPER_IDS.append(user_id)
        
        # Update the environment variable
        dev_ids_str = os.environ.get("DEVELOPER_IDS", "")
        current_ids = [id.strip() for id in dev_ids_str.split(",") if id.strip()]
        
        if str(user_id) not in current_ids:
            current_ids.append(str(user_id))
            
        # Update environment variable
        os.environ["DEVELOPER_IDS"] = ",".join(current_ids)
        
        logger.info(f"Added user {user_id} to developers list")
        return True
    
    except Exception as e:
        logger.error(f"Error adding developer: {e}")
        return False

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
    - today/tomorrow/days of week + optional time (e.g., tomorrow 3pm, Friday 10:30)
    - specific dates (e.g., Feb 15, 2025-04-20)
    - absolute times (e.g., 3pm, 15:00)
    """
    time_str = time_str.strip().lower()
    
    # Get current datetime for reference
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Pattern for relative time formats
    # Pattern for Xh Ym format
    pattern_short = r'(?:(\d+)h)?\s*(?:(\d+)m)?'
    # Pattern for X hours Y minutes format
    pattern_long = r'(?:(\d+)\s*hours?)?\s*(?:(\d+)\s*minutes?)?'
    # Pattern for X:Y format (HH:MM)
    pattern_colon = r'(\d+):(\d+)'
    
    # Try short format (1h 30m)
    match = re.fullmatch(pattern_short, time_str)
    if match and (match.group(1) or match.group(2)):
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    # Try long format (1 hour 30 minutes)
    match = re.fullmatch(pattern_long, time_str)
    if match and (match.group(1) or match.group(2)):
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    # Try colon format (1:30)
    match = re.fullmatch(pattern_colon, time_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        delta = timedelta(hours=hours, minutes=minutes)
        return get_current_time() + delta.total_seconds()
    
    # Try "today/tomorrow" formats with times
    days_offset = 0
    remaining_time_str = time_str
    
    # Check for today/tomorrow keywords
    if time_str.startswith('today'):
        days_offset = 0
        remaining_time_str = time_str[5:].strip()  # Remove "today" and continue processing
    elif time_str.startswith('tomorrow'):
        days_offset = 1
        remaining_time_str = time_str[8:].strip()  # Remove "tomorrow" and continue processing
    else:
        # Check for day of week
        days_of_week = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        for day_name, day_num in days_of_week.items():
            if time_str.startswith(day_name):
                # Calculate days until the next occurrence of this day
                current_day = now.weekday()
                days_until = (day_num - current_day) % 7
                
                # If it's the same day and we specify a time that's already passed, 
                # we mean next week
                if days_until == 0 and len(time_str) > len(day_name):
                    possible_time = time_str[len(day_name):].strip()
                    time_delta = parse_time_of_day(possible_time)
                    if time_delta:
                        day_time = today + time_delta
                        if day_time.time() < now.time():
                            days_until = 7
                
                days_offset = days_until
                remaining_time_str = time_str[len(day_name):].strip()
                break
    
        # Check for specific date formats (MM/DD, MM-DD, Month Day)
        if days_offset == 0:  # No day of week was found
            date_patterns = [
                # MM/DD or MM/DD/YY or MM/DD/YYYY
                r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?',
                # MM-DD or MM-DD-YY or MM-DD-YYYY
                r'(\d{1,2})-(\d{1,2})(?:-(\d{2,4}))?',
                # Month Day or Month Day, Year
                r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* (\d{1,2})(?:,? (\d{4}))?'
            ]
            
            month_names = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            for pattern in date_patterns:
                match = re.search(pattern, time_str)
                if match:
                    parts = list(match.groups())
                    
                    try:
                        # For month name format
                        if parts[0].lower() in month_names:
                            month = month_names[parts[0].lower()]
                            day = int(parts[1])
                            year = int(parts[2]) if parts[2] else now.year
                            
                            # Adjust 2-digit year
                            if year < 100:
                                year += 2000
                        else:
                            # For numeric formats
                            month = int(parts[0])
                            day = int(parts[1])
                            year = int(parts[2]) if parts[2] else now.year
                            
                            # Adjust 2-digit year
                            if year < 100:
                                year += 2000
                        
                        # Create the date
                        target_date = datetime(year, month, day)
                        
                        # If the date is in the past, assume next year
                        if target_date.date() < now.date():
                            if month < now.month or (month == now.month and day < now.day):
                                target_date = datetime(year + 1, month, day)
                        
                        # Extract any time information that might be after the date
                        time_part = time_str[match.end():].strip()
                        
                        # Default to noon if no time specified
                        if not time_part:
                            target_date = target_date.replace(hour=12, minute=0)
                        else:
                            # Try to parse the time part
                            time_delta = parse_time_of_day(time_part)
                            if time_delta:
                                # Add the time delta to midnight of the target date
                                target_date = datetime.combine(target_date.date(), datetime.min.time())
                                target_date = target_date + time_delta
                        
                        return target_date.timestamp()
                    except ValueError:
                        # Invalid date, skip this match
                        pass
    
    # Process time of day if we have a days offset or if we're still dealing with the original time string
    if days_offset > 0 or remaining_time_str:
        # Try to parse as a time of day
        time_delta = parse_time_of_day(remaining_time_str)
        if time_delta:
            # Calculate the target date (today + days_offset)
            target_date = today + timedelta(days=days_offset)
            
            # Add the time delta to the target date
            target_datetime = datetime.combine(target_date.date(), datetime.min.time())
            target_datetime = target_datetime + time_delta
            
            # If it's today and the time has passed, move to tomorrow
            if days_offset == 0 and target_datetime < now:
                target_datetime += timedelta(days=1)
            
            return target_datetime.timestamp()
    
    # Try to parse just as a time of day (for today)
    if not remaining_time_str:
        remaining_time_str = time_str
        
    time_delta = parse_time_of_day(remaining_time_str)
    if time_delta:
        # Add the time delta to today at midnight
        target_datetime = datetime.combine(today.date(), datetime.min.time())
        target_datetime = target_datetime + time_delta
        
        # If the time has already passed today, assume tomorrow
        if target_datetime < now:
            target_datetime += timedelta(days=1)
        
        return target_datetime.timestamp()
    
    return None

def parse_time_of_day(time_str: str) -> Optional[timedelta]:
    """Parse a string into a time object (hour:minute)
    
    Formats supported:
    - 3pm, 3 pm, 3:00pm, 3:00 pm
    - 15:00, 15h, 15h00
    
    Returns:
        Optional[timedelta]: Time of day as a timedelta from midnight, or None if parsing fails
    """
    time_str = time_str.strip().lower()
    
    # Try 12-hour format with am/pm
    am_pm_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)'
    match = re.fullmatch(am_pm_pattern, time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        am_pm = match.group(3)
        
        # Convert to 24-hour format
        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return timedelta(hours=hour, minutes=minute)
    
    # Try 24-hour format (15:00)
    hour_min_pattern = r'(\d{1,2}):(\d{2})'
    match = re.fullmatch(hour_min_pattern, time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return timedelta(hours=hour, minutes=minute)
    
    # Try 24-hour format with 'h' (15h00)
    hour_h_min_pattern = r'(\d{1,2})h(\d{2})?'
    match = re.fullmatch(hour_h_min_pattern, time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return timedelta(hours=hour, minutes=minute)
    
    # Just hour (3, 15)
    hour_only_pattern = r'(\d{1,2})'
    match = re.fullmatch(hour_only_pattern, time_str)
    if match:
        hour = int(match.group(1))
        
        # Assume hours >= 13 are in 24-hour format, others need am/pm
        # which should have been caught by the am_pm pattern
        if 13 <= hour <= 23:
            return timedelta(hours=hour)
    
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

def log_command_usage(chat_id, chat_type, user_id, command, success=True):
    """Log command usage for analytics and debugging
    
    Args:
        chat_id: The ID of the chat where the command was executed
        chat_type: The type of chat (private, group, etc.)
        user_id: The ID of the user who executed the command
        command: The command that was executed
        success: Whether the command was executed successfully
    """
    try:
        with open("command_usage.log", "a") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_dev = is_developer(user_id)
            status = "SUCCESS" if success else "FAILURE"
            f.write(f"[{now}] CHAT:{chat_id} TYPE:{chat_type} USER:{user_id} DEV:{is_dev} CMD:{command} STATUS:{status}\n")
    except Exception as e:
        logger.error(f"Error logging command usage: {e}")
