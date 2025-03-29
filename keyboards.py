from typing import List, Dict, Any
from telegram import InlineKeyboardButton

def get_task_list_keyboard(tasks: List[Dict[str, Any]], action_type: str = "default") -> List[List[InlineKeyboardButton]]:
    """Generate keyboard buttons for task lists based on action type"""
    keyboard = []
    
    for i, task in enumerate(tasks):
        row = []
        
        if action_type == "default":
            # Default keyboard for task list has Done and Delete buttons
            row.append(InlineKeyboardButton("✅ Done", callback_data=f"done:{i}"))
            row.append(InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{i}"))
            row.append(InlineKeyboardButton("⏰ Remind", callback_data=f"remind:{i}"))
        elif action_type == "done":
            # Only Done button
            row.append(InlineKeyboardButton(f"✅ Task {i+1}", callback_data=f"done:{i}"))
        elif action_type == "delete":
            # Only Delete button
            row.append(InlineKeyboardButton(f"🗑️ Task {i+1}", callback_data=f"delete:{i}"))
        elif action_type == "remind":
            # Only Remind button
            row.append(InlineKeyboardButton(f"⏰ Task {i+1}", callback_data=f"remind:{i}"))
        
        keyboard.append(row)
    
    return keyboard

def get_confirmation_keyboard(action: str) -> List[List[InlineKeyboardButton]]:
    """Generate confirmation keyboard with Yes/No buttons"""
    if action == "clear_all":
        # Confirmation for clearing all tasks
        return [
            [
                InlineKeyboardButton("✅ Yes, clear all", callback_data="confirm_clear"),
                InlineKeyboardButton("❌ No, cancel", callback_data="cancel_clear")
            ]
        ]
    else:
        # Confirmation for other actions (like deleting a specific task)
        return [
            [
                InlineKeyboardButton("✅ Yes", callback_data="confirm_delete"),
                InlineKeyboardButton("❌ No", callback_data="cancel_delete")
            ]
        ]

def get_time_selection_keyboard(task_index: int) -> List[List[InlineKeyboardButton]]:
    """Generate keyboard for selecting reminder time"""
    # Define common reminder times (in minutes)
    times = [
        ("15m", 15),
        ("30m", 30),
        ("1h", 60),
        ("3h", 180),
        ("6h", 360),
        ("12h", 720),
        ("24h", 1440)
    ]
    
    keyboard = []
    row = []
    
    # Create buttons for each time option
    for i, (label, minutes) in enumerate(times):
        row.append(InlineKeyboardButton(label, callback_data=f"time:{task_index}:{minutes}"))
        
        # Create new row every 3 buttons
        if (i + 1) % 3 == 0 or i == len(times) - 1:
            keyboard.append(row)
            row = []
    
    return keyboard

def get_settings_keyboard(settings: Dict[str, Any]) -> List[List[InlineKeyboardButton]]:
    """Generate keyboard for settings menu"""
    # Default reminder setting
    reminder_default = settings.get('reminder_default', False)
    reminder_text = "🔔 Default Reminder: ON" if reminder_default else "🔕 Default Reminder: OFF"
    
    # Sort order setting
    sort_by = settings.get('sort_by', 'date')
    sort_text = "📅 Sort by: Date" if sort_by == 'date' else "⭐ Sort by: Priority"
    
    keyboard = [
        [InlineKeyboardButton(reminder_text, callback_data="setting:reminder_default")],
        [InlineKeyboardButton(sort_text, callback_data="setting:sort_by")],
        [InlineKeyboardButton("🔙 Back", callback_data="setting:back")]
    ]
    
    return keyboard
