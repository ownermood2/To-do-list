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
    # Define common reminder times (in minutes) with more friendly labels
    times = [
        ("⏱️ 15 minutes", 15),
        ("⏱️ 30 minutes", 30),
        ("🕐 1 hour", 60),
        ("🕒 3 hours", 180),
        ("🕕 6 hours", 360),
        ("🕛 12 hours", 720),
        ("📅 Tomorrow", 1440)
    ]
    
    # Define special time options for group tasks
    group_times = [
        ("⏰ End of day", 0),  # Special value for end of day
        ("📆 This weekend", -1),  # Special value for weekend
        ("🗓️ Next week", -2)   # Special value for next week
    ]
    
    keyboard = []
    
    # First section: Quick options (most common)
    keyboard.append([
        InlineKeyboardButton(times[0][0], callback_data=f"time:{task_index}:{times[0][1]}"),
        InlineKeyboardButton(times[1][0], callback_data=f"time:{task_index}:{times[1][1]}")
    ])
    
    keyboard.append([
        InlineKeyboardButton(times[2][0], callback_data=f"time:{task_index}:{times[2][1]}"),
        InlineKeyboardButton(times[3][0], callback_data=f"time:{task_index}:{times[3][1]}")
    ])
    
    # Second section: Longer periods
    keyboard.append([
        InlineKeyboardButton(times[4][0], callback_data=f"time:{task_index}:{times[4][1]}"),
        InlineKeyboardButton(times[5][0], callback_data=f"time:{task_index}:{times[5][1]}")
    ])
    
    # Third section: Special timing options (good for groups)
    keyboard.append([InlineKeyboardButton(times[6][0], callback_data=f"time:{task_index}:{times[6][1]}")])
    
    keyboard.append([
        InlineKeyboardButton(group_times[0][0], callback_data=f"special_time:{task_index}:{group_times[0][1]}"),
        InlineKeyboardButton(group_times[1][0], callback_data=f"special_time:{task_index}:{group_times[1][1]}")
    ])
    
    keyboard.append([InlineKeyboardButton(group_times[2][0], callback_data=f"special_time:{task_index}:{group_times[2][1]}")])
    
    # Add custom time option
    keyboard.append([InlineKeyboardButton("⚙️ Custom time", callback_data=f"custom_time:{task_index}")])
    
    # Add cancel option (important for UX)
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_reminder")])
    
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
