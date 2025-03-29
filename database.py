import json
import logging
import os
from typing import Dict, List, Any
from config import DATA_FILE

logger = logging.getLogger(__name__)

# In-memory data storage
_data = {}

def initialize_database() -> None:
    """Initialize the database by loading data from the JSON file if it exists"""
    global _data
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                _data = json.load(file)
                logger.info(f"Loaded data for {len(_data)} chats from {DATA_FILE}")
        else:
            _data = {}
            logger.info(f"No existing data file found. Starting with empty database.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        _data = {}

def save_data(data=None) -> bool:
    """Save the current data to the JSON file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data if data is not None else _data, file, ensure_ascii=False, indent=2)
        logger.debug("Data saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False

def get_data() -> Dict:
    """Get the current data"""
    return _data

def get_chat_data(chat_id: int) -> Dict:
    """Get data for a specific chat"""
    chat_id_str = str(chat_id)  # Convert to string for JSON compatibility
    if chat_id_str not in _data:
        _data[chat_id_str] = {
            'type': 'user',  # Default to user, will be updated if it's a group
            'tasks': [],
            'settings': {
                'reminder_default': False,
                'reminder_time': 3600,  # Default reminder time (1 hour)
                'sort_by': 'date',  # Sort tasks by date by default
                'theme': 'default',  # UI theme preference
                'notification_level': 'all',  # Notification settings: all, important, none
                'time_format': '24h',  # Time format: 12h or 24h
                'categories': ['Work', 'Personal', 'Shopping', 'Health', 'Other'],  # Default categories
                'language': 'en',  # User interface language
                'auto_clean': True,  # Automatically clean old messages
                'auto_clean_days': 3,  # Days to keep messages before cleaning
            },
            'stats': {
                'tasks_added': 0,
                'tasks_completed': 0,
                'last_active': iso_now(),
                'streaks': {
                    'current': 0,
                    'longest': 0,
                    'last_completion_date': None
                }
            }
        }
        save_data()
    return _data[chat_id_str]

def update_chat_data(chat_id: int, chat_data: Dict) -> None:
    """Update data for a specific chat"""
    chat_id_str = str(chat_id)  # Convert to string for JSON compatibility
    _data[chat_id_str] = chat_data
    save_data()

def add_task(chat_id: int, task_text: str, due_date=None, reminder=None, priority=None, 
            category=None, assignee=None, notes=None) -> Dict:
    """Add a new task for a chat with enhanced properties"""
    chat_data = get_chat_data(chat_id)
    
    # Create new task with advanced properties
    task = {
        'text': task_text,
        'done': False,
        'date_added': iso_now(),
        'active': True,
        'priority': priority or 'normal',  # 'high', 'normal', or 'low'
        'category': category or 'default',
        'notes': notes or '',
        'progress': 0,  # Track progress from 0-100%
        'attachments': [],
        'updated_at': iso_now(),
    }
    
    # Add optional fields
    if due_date:
        task['due_date'] = due_date
    if reminder:
        task['reminder'] = reminder
    if assignee:
        task['assignee'] = assignee  # For group task assignment
    
    chat_data['tasks'].append(task)
    update_chat_data(chat_id, chat_data)
    
    return task

def get_tasks(chat_id: int, include_done: bool = False) -> List[Dict]:
    """Get all active tasks for a chat"""
    chat_data = get_chat_data(chat_id)
    tasks = chat_data.get('tasks', [])
    
    if not include_done:
        tasks = [task for task in tasks if task.get('active', True) and not task.get('done', False)]
    
    return tasks

def mark_task_done(chat_id: int, task_index: int) -> bool:
    """Mark a task as done"""
    chat_data = get_chat_data(chat_id)
    tasks = chat_data.get('tasks', [])
    
    if 0 <= task_index < len(tasks):
        tasks[task_index]['done'] = True
        update_chat_data(chat_id, chat_data)
        return True
    return False

def delete_task(chat_id: int, task_index: int) -> bool:
    """Delete a task"""
    chat_data = get_chat_data(chat_id)
    tasks = chat_data.get('tasks', [])
    
    if 0 <= task_index < len(tasks):
        # Instead of deleting, mark as inactive
        tasks[task_index]['active'] = False
        update_chat_data(chat_id, chat_data)
        return True
    return False

def clear_tasks(chat_id: int) -> int:
    """Clear all tasks for a chat (mark as inactive)"""
    chat_data = get_chat_data(chat_id)
    tasks = chat_data.get('tasks', [])
    
    count = 0
    for task in tasks:
        if task.get('active', True):
            task['active'] = False
            count += 1
    
    update_chat_data(chat_id, chat_data)
    return count

def set_reminder(chat_id: int, task_index: int, reminder_time: float) -> bool:
    """Set a reminder for a task"""
    chat_data = get_chat_data(chat_id)
    tasks = chat_data.get('tasks', [])
    
    if 0 <= task_index < len(tasks):
        tasks[task_index]['reminder'] = reminder_time
        update_chat_data(chat_id, chat_data)
        return True
    return False

def update_settings(chat_id: int, settings: Dict) -> None:
    """Update settings for a chat"""
    chat_data = get_chat_data(chat_id)
    
    if 'settings' not in chat_data:
        chat_data['settings'] = {}
    
    chat_data['settings'].update(settings)
    update_chat_data(chat_id, chat_data)

def update_chat_type(chat_id: int, chat_type: str) -> None:
    """Update the type of a chat (user, group, etc.)"""
    chat_data = get_chat_data(chat_id)
    chat_data['type'] = chat_type
    update_chat_data(chat_id, chat_data)

def get_all_chat_ids() -> List[str]:
    """Get all chat IDs"""
    return list(_data.keys())

def get_stats() -> Dict[str, Any]:
    """Get statistics about the bot usage"""
    stats = {
        'total_chats': len(_data),
        'total_users': sum(1 for chat_id, data in _data.items() if data.get('type') == 'user'),
        'total_groups': sum(1 for chat_id, data in _data.items() if data.get('type') in ['group', 'supergroup']),
        'total_tasks': sum(len(data.get('tasks', [])) for data in _data.values()),
        'active_tasks': sum(
            sum(1 for task in data.get('tasks', []) if task.get('active', True) and not task.get('done', False))
            for data in _data.values()
        ),
        'completed_tasks': sum(
            sum(1 for task in data.get('tasks', []) if task.get('done', True) and task.get('active', True))
            for data in _data.values()
        )
    }
    return stats

def iso_now() -> str:
    """Get current date and time in ISO format"""
    from datetime import datetime
    return datetime.now().isoformat()
