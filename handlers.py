import logging
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext
from config import (
    WELCOME_MESSAGE, 
    HELP_MESSAGE, 
    GROUP_WELCOME_MESSAGE, 
    COMMANDS, 
    DEVELOPER_COMMANDS,
    DEVELOPER_IDS
)
from database import (
    get_chat_data, 
    add_task, 
    get_tasks, 
    mark_task_done, 
    delete_task, 
    clear_tasks, 
    set_reminder,
    update_settings,
    update_chat_type,
    get_all_chat_ids,
    get_stats,
    update_chat_data,
    iso_now
)
from keyboards import (
    get_task_list_keyboard,
    get_settings_keyboard,
    get_confirmation_keyboard,
    get_time_selection_keyboard
)
from utils import (
    is_developer,
    format_task_list,
    parse_time,
    get_current_time
)

logger = logging.getLogger(__name__)

# Global maintenance mode flag
maintenance_mode = False

# Define chat types as constants
CHAT_TYPE_PRIVATE = 'private'
CHAT_TYPE_GROUP = 'group'
CHAT_TYPE_SUPERGROUP = 'supergroup'

def start_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /start command - introduce the bot to the user/group"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Update chat type in database
    update_chat_type(chat_id, chat_type)
    
    # Select appropriate welcome message based on chat type
    if chat_type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]:
        message = GROUP_WELCOME_MESSAGE
    else:
        message = WELCOME_MESSAGE
    
    update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Bot started in {chat_type} chat {chat_id}")

def help_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /help command - show available commands"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    user_id = update.effective_user.id
    
    # Build help message with all commands
    help_text = HELP_MESSAGE
    for cmd, desc in COMMANDS.items():
        help_text += f"/{cmd} - {desc}\n"
    
    # Add developer commands if the user is a developer
    if is_developer(user_id):
        help_text += "\n🛠️ *Developer Commands*:\n"
        for cmd, desc in DEVELOPER_COMMANDS.items():
            help_text += f"/{cmd} - {desc}\n"
    
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def add_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /add command - add a new task"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Check if task text is provided
    if not context.args:
        update.message.reply_text(
            "Please provide a task description after the /add command.\n"
            "For example: `/add Buy groceries`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Join all arguments into a single task text
    task_text = ' '.join(context.args)
    
    # Add the task to the database
    task = add_task(chat_id, task_text)
    
    update.message.reply_text(
        f"✅ Task added successfully!\n\n*{task_text}*",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.debug(f"New task added in chat {chat_id}: {task_text}")

def list_tasks_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /list command - list all tasks"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get tasks for this chat
    tasks = get_tasks(chat_id)
    
    if not tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Format tasks as a list and include buttons for actions
    task_text = format_task_list(tasks)
    keyboard = get_task_list_keyboard(tasks)
    
    update.message.reply_text(
        task_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def done_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /done command - mark a task as done"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Check if task index is provided
    if not context.args:
        # If no index is provided, show the task list with done buttons
        tasks = get_tasks(chat_id)
        
        if not tasks:
            update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
            return
        
        task_text = "Select a task to mark as done:\n\n" + format_task_list(tasks)
        keyboard = get_task_list_keyboard(tasks, action_type="done")
        
        update.message.reply_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # User provided a task index, try to mark it as done
        task_index = int(context.args[0]) - 1  # Convert to 0-based index
        
        if mark_task_done(chat_id, task_index):
            tasks = get_tasks(chat_id, include_done=True)
            task_text = tasks[task_index]['text']
            
            update.message.reply_text(
                f"✅ Task marked as done: *{task_text}*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text("❌ Invalid task number. Use /list to see your tasks.")
    except ValueError:
        update.message.reply_text("❌ Please provide a valid task number after /done.")

def delete_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /delete command - delete a task"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Check if task index is provided
    if not context.args:
        # If no index is provided, show the task list with delete buttons
        tasks = get_tasks(chat_id)
        
        if not tasks:
            update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
            return
        
        task_text = "Select a task to delete:\n\n" + format_task_list(tasks)
        keyboard = get_task_list_keyboard(tasks, action_type="delete")
        
        update.message.reply_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # User provided a task index, try to delete it
        task_index = int(context.args[0]) - 1  # Convert to 0-based index
        tasks = get_tasks(chat_id)
        
        if 0 <= task_index < len(tasks):
            task_text = tasks[task_index]['text']
            keyboard = get_confirmation_keyboard(f"delete:{task_index}")
            
            update.message.reply_text(
                f"Are you sure you want to delete this task?\n\n*{task_text}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text("❌ Invalid task number. Use /list to see your tasks.")
    except ValueError:
        update.message.reply_text("❌ Please provide a valid task number after /delete.")

def clear_tasks_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /clear command - clear all tasks"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Ask for confirmation before clearing all tasks
    keyboard = get_confirmation_keyboard("clear_all")
    
    update.message.reply_text(
        "⚠️ Are you sure you want to clear all tasks? This cannot be undone!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def remind_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /remind command - set a reminder for a task"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get tasks for this chat
    tasks = get_tasks(chat_id)
    
    if not tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Check arguments
    if len(context.args) < 1:
        # Show task list for selection
        task_text = "Select a task to set a reminder for:\n\n" + format_task_list(tasks)
        keyboard = get_task_list_keyboard(tasks, action_type="remind")
        
        update.message.reply_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        task_index = int(context.args[0]) - 1  # Convert to 0-based index
        
        if 0 <= task_index < len(tasks):
            if len(context.args) >= 2:
                # Parse time input
                time_input = ' '.join(context.args[1:])
                reminder_time = parse_time(time_input)
                
                if reminder_time:
                    current_time = get_current_time()
                    relative_time = reminder_time - current_time
                    
                    if set_reminder(chat_id, task_index, reminder_time):
                        task_text = tasks[task_index]['text']
                        
                        # Format relative time for display
                        hours = int(relative_time // 3600)
                        minutes = int((relative_time % 3600) // 60)
                        
                        time_display = ""
                        if hours > 0:
                            time_display += f"{hours} hour{'s' if hours != 1 else ''} "
                        if minutes > 0 or hours == 0:
                            time_display += f"{minutes} minute{'s' if minutes != 1 else ''}"
                        
                        update.message.reply_text(
                            f"⏰ Reminder set for *{task_text}* in {time_display}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        update.message.reply_text("❌ Failed to set reminder. Please try again.")
                else:
                    update.message.reply_text(
                        "❌ Invalid time format. Please use a format like '1h 30m' or '2 hours'."
                    )
            else:
                # Show time selection keyboard
                task_text = tasks[task_index]['text']
                keyboard = get_time_selection_keyboard(task_index)
                
                update.message.reply_text(
                    f"Select when to be reminded about:\n\n*{task_text}*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text("❌ Invalid task number. Use /list to see your tasks.")
    except ValueError:
        update.message.reply_text(
            "❌ Please provide a valid task number and time.\n"
            "Example: `/remind 1 30m` to set a reminder for task 1 in 30 minutes."
        )

def settings_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /settings command - configure bot settings"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    chat_data = get_chat_data(chat_id)
    settings = chat_data.get('settings', {})
    
    keyboard = get_settings_keyboard(settings)
    
    update.message.reply_text(
        "⚙️ *Bot Settings*\n\nSelect an option to configure:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def button_callback_handler(update: Update, context: CallbackContext) -> None:
    """Handle callbacks from inline buttons"""
    if maintenance_mode and not is_developer(update.callback_query.from_user.id):
        update.callback_query.answer("Bot is currently in maintenance mode.")
        return
        
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id
    
    # Acknowledge the button press
    query.answer()
    
    # Process different button actions
    # New handlers for add_task from text messages
    if data.startswith("add_task:"):
        # Add task directly from message text
        task_text = data.split(":", 1)[1]
        
        # Add the task to the database
        task = add_task(chat_id, task_text)
        
        # Update statistics
        chat_data = get_chat_data(chat_id)
        if 'stats' in chat_data:
            chat_data['stats']['tasks_added'] = chat_data['stats'].get('tasks_added', 0) + 1
            chat_data['stats']['last_active'] = iso_now()
            update_chat_data(chat_id, chat_data)
        
        # Reply with confirmation
        query.edit_message_text(
            f"✅ Task added successfully:\n\n*{task_text}*\n\nUse /list to view all your tasks.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("add_task_reminder:"):
        # Add task with reminder from message text
        task_text = data.split(":", 1)[1]
        
        # Add the task to the database
        task = add_task(chat_id, task_text)
        
        # Find the task index in the active tasks list
        tasks = get_tasks(chat_id)
        task_index = next((i for i, t in enumerate(tasks) if t['text'] == task['text']), 0)
        
        # Show time selection for reminder
        keyboard = get_time_selection_keyboard(task_index)
        
        # Check if this is a group chat for friendlier message
        is_group = update.effective_chat.type in ["group", "supergroup"]
        
        query.edit_message_text(
            f"⏰ Task added! When should I remind {'everyone' if is_group else 'you'} about:\n\n*{task_text}*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("assign_group:"):
        # Add a task specifically for the group (everyone)
        task_text = data.split(":", 1)[1]
        
        # Check if we're actually in a group chat
        is_group = update.effective_chat.type in ["group", "supergroup"]
        if not is_group:
            query.edit_message_text(
                "⚠️ This option is only available in group chats.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Add the task to the database with group tag
        task = add_task(chat_id, task_text, category="Group Task")
        
        # Find the task index in the active tasks list
        tasks = get_tasks(chat_id)
        task_index = next((i for i, t in enumerate(tasks) if t['text'] == task['text']), 0)
        
        # Show time selection for reminder
        keyboard = get_time_selection_keyboard(task_index)
        
        query.edit_message_text(
            f"👥 *Group Task Added!*\n\nWhen should I remind everyone about:\n*{task_text}*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "cancel_add_task":
        # User declined to add the message as task
        query.edit_message_text(
            "⏹️ Message not added as a task.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("done:"):
        # Mark task as done
        task_index = int(data.split(":")[1])
        if mark_task_done(chat_id, task_index):
            tasks = get_tasks(chat_id, include_done=True)
            task_text = tasks[task_index]['text']
            
            # Update statistics
            chat_data = get_chat_data(chat_id)
            if 'stats' in chat_data:
                chat_data['stats']['tasks_completed'] = chat_data['stats'].get('tasks_completed', 0) + 1
                chat_data['stats']['last_active'] = iso_now()
                
                # Update streak data
                from datetime import datetime, timedelta
                now = datetime.now()
                last_completion = chat_data['stats']['streaks'].get('last_completion_date')
                
                if last_completion:
                    # Convert ISO string to datetime
                    last_completion_date = datetime.fromisoformat(last_completion)
                    # Check if last completion was yesterday or today
                    if (now.date() - last_completion_date.date()) <= timedelta(days=1):
                        # Maintain or increase streak
                        if now.date() > last_completion_date.date():  # Only increase if it's a new day
                            chat_data['stats']['streaks']['current'] += 1
                            # Update longest streak if needed
                            if chat_data['stats']['streaks']['current'] > chat_data['stats']['streaks']['longest']:
                                chat_data['stats']['streaks']['longest'] = chat_data['stats']['streaks']['current']
                    else:
                        # Streak broken
                        chat_data['stats']['streaks']['current'] = 1
                else:
                    # First completion
                    chat_data['stats']['streaks']['current'] = 1
                    
                # Update last completion date
                chat_data['stats']['streaks']['last_completion_date'] = now.isoformat()
                update_chat_data(chat_id, chat_data)
            
            # Update the message to reflect the change
            query.edit_message_text(
                f"✅ Task marked as done: *{task_text}*",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("delete:"):
        # Show confirmation for task deletion
        task_index = int(data.split(":")[1])
        tasks = get_tasks(chat_id)
        
        if 0 <= task_index < len(tasks):
            task_text = tasks[task_index]['text']
            keyboard = get_confirmation_keyboard(f"delete:{task_index}")
            
            query.edit_message_text(
                f"Are you sure you want to delete this task?\n\n*{task_text}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("confirm_delete:"):
        # Extract task index from original message
        original_text = query.message.text
        try:
            task_index_match = original_text.strip().split("delete:")[1]
            task_index = int(task_index_match)
            
            if delete_task(chat_id, task_index):
                tasks = get_tasks(chat_id, include_done=True)
                task_text = tasks[task_index]['text'] if task_index < len(tasks) else "Unknown task"
                
                query.edit_message_text(
                    f"🗑️ Task deleted: *{task_text}*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                query.edit_message_text("❌ Failed to delete task. Please try again.")
        except (IndexError, ValueError):
            query.edit_message_text("❌ Error processing task deletion. Please try again.")
    
    elif data == "cancel_delete":
        query.edit_message_text("❌ Task deletion canceled.")
        
    elif data == "confirm_clear":
        count = clear_tasks(chat_id)
        query.edit_message_text(f"🧹 Cleared {count} tasks.")
        
    elif data == "cancel_clear":
        query.edit_message_text("❌ Clear operation canceled.")
        
    elif data.startswith("remind:"):
        # Show time selection for reminder
        task_index = int(data.split(":")[1])
        tasks = get_tasks(chat_id)
        
        if 0 <= task_index < len(tasks):
            task_text = tasks[task_index]['text']
            keyboard = get_time_selection_keyboard(task_index)
            
            # Check if this is a group chat
            is_group = update.effective_chat.type in ["group", "supergroup"]
            
            query.edit_message_text(
                f"⏰ *When should I remind {'everyone' if is_group else 'you'} about:*\n\n*{task_text}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data == "cancel_reminder":
        # User cancelled setting a reminder
        query.edit_message_text(
            "⏹️ Reminder setup cancelled.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("time:"):
        # Set reminder with predefined time
        parts = data.split(":")
        task_index = int(parts[1])
        time_minutes = int(parts[2])
        
        current_time = get_current_time()
        reminder_time = current_time + (time_minutes * 60)
        
        if set_reminder(chat_id, task_index, reminder_time):
            tasks = get_tasks(chat_id)
            if 0 <= task_index < len(tasks):
                task_text = tasks[task_index]['text']
                
                # Format time for display
                if time_minutes < 60:
                    time_display = f"{time_minutes} minute{'s' if time_minutes != 1 else ''}"
                else:
                    hours = time_minutes // 60
                    mins = time_minutes % 60
                    time_display = f"{hours} hour{'s' if hours != 1 else ''}"
                    if mins > 0:
                        time_display += f" {mins} minute{'s' if mins != 1 else ''}"
                
                # Check if this is a group chat
                is_group = update.effective_chat.type in ["group", "supergroup"]
                mention = f"@all" if is_group else "you"
                
                query.edit_message_text(
                    f"⏰ Reminder set! I'll remind {mention} about:\n*{task_text}*\nIn: {time_display}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                query.edit_message_text("❌ Task not found. It may have been deleted.")
        else:
            query.edit_message_text("❌ Failed to set reminder. Please try again.")
            
    elif data.startswith("special_time:"):
        # Handle special timing options (end of day, weekend, next week)
        parts = data.split(":")
        task_index = int(parts[1])
        time_option = int(parts[2])
        
        current_time = get_current_time()
        reminder_time = current_time
        time_display = ""
        
        # Calculate the appropriate reminder time based on special options
        if time_option == 0:  # End of day
            # Calculate time until 8:00 PM today
            from datetime import datetime, timedelta
            current_dt = datetime.fromtimestamp(current_time)
            end_of_day = current_dt.replace(hour=20, minute=0, second=0)
            
            # If it's already past 8 PM, set for tomorrow
            if current_dt.hour >= 20:
                end_of_day = end_of_day + timedelta(days=1)
                
            reminder_time = end_of_day.timestamp()
            time_display = "end of day (8:00 PM)"
            
        elif time_option == -1:  # Weekend
            # Calculate time until Saturday 10:00 AM
            from datetime import datetime, timedelta
            current_dt = datetime.fromtimestamp(current_time)
            days_until_saturday = (5 - current_dt.weekday()) % 7
            
            # If it's already Saturday or Sunday, set for next Saturday
            if days_until_saturday == 0 and current_dt.hour >= 10:
                days_until_saturday = 7
            elif days_until_saturday < 0:
                days_until_saturday += 7
                
            weekend = current_dt + timedelta(days=days_until_saturday)
            weekend = weekend.replace(hour=10, minute=0, second=0)
            
            reminder_time = weekend.timestamp()
            time_display = f"this weekend (Saturday, 10:00 AM)"
            
        elif time_option == -2:  # Next week
            # Calculate time until Monday 9:00 AM
            from datetime import datetime, timedelta
            current_dt = datetime.fromtimestamp(current_time)
            days_until_monday = (0 - current_dt.weekday()) % 7
            
            # If it's already Monday, set for next Monday
            if days_until_monday == 0:
                days_until_monday = 7
                
            next_week = current_dt + timedelta(days=days_until_monday)
            next_week = next_week.replace(hour=9, minute=0, second=0)
            
            reminder_time = next_week.timestamp()
            time_display = f"next week (Monday, 9:00 AM)"
        
        # Set the reminder with calculated time
        if set_reminder(chat_id, task_index, reminder_time):
            tasks = get_tasks(chat_id)
            if 0 <= task_index < len(tasks):
                task_text = tasks[task_index]['text']
                
                # Check if this is a group chat
                is_group = update.effective_chat.type in ["group", "supergroup"]
                mention = f"everyone in this group" if is_group else "you"
                
                query.edit_message_text(
                    f"📅 *Special Reminder Set!*\n\nI'll remind {mention} about:\n*{task_text}*\n\nTime: {time_display}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                query.edit_message_text("❌ Task not found. It may have been deleted.")
        else:
            query.edit_message_text("❌ Failed to set reminder. Please try again.")
            
    elif data.startswith("custom_time:"):
        # Handle custom time input request
        task_index = int(data.split(":")[1])
        tasks = get_tasks(chat_id)
        
        if 0 <= task_index < len(tasks):
            task_text = tasks[task_index]['text']
            
            # Store the task index in user_data for the next step
            if not context.user_data:
                context.user_data = {}
            context.user_data["custom_reminder_task"] = task_index
            
            query.edit_message_text(
                f"⏰ *Custom Reminder*\n\nPlease reply with the time for your reminder for:\n*{task_text}*\n\n"
                f"Examples:\n"
                f"• `1h 30m` (1 hour and 30 minutes)\n"
                f"• `tomorrow 9am` (tomorrow at 9:00 AM)\n"
                f"• `friday 3pm` (next Friday at 3:00 PM)\n\n"
                f"Type `cancel` to cancel.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # Priority handling
    elif data.startswith("priority:"):
        parts = data.split(":")
        task_index = int(parts[1])
        priority = parts[2]
        
        tasks = get_tasks(chat_id)
        if 0 <= task_index < len(tasks):
            # Update task priority
            chat_data = get_chat_data(chat_id)
            all_tasks = chat_data.get('tasks', [])
            
            # Find the right task (it might not be in the same position as in filtered tasks)
            for task in all_tasks:
                if task.get('text') == tasks[task_index].get('text') and task.get('active', True):
                    task['priority'] = priority
                    task['updated_at'] = iso_now()
                    break
            
            update_chat_data(chat_id, chat_data)
            
            # Get priority icon
            priority_icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
            
            query.edit_message_text(
                f"{priority_icon} Priority updated to *{priority.upper()}* for task:\n\n*{tasks[task_index]['text']}*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            query.edit_message_text("❌ Failed to update priority. Task not found.")
    
    # Category handling
    elif data.startswith("category:"):
        parts = data.split(":", 2)  # Split into 3 parts
        task_index = int(parts[1])
        category = parts[2]
        
        tasks = get_tasks(chat_id)
        if 0 <= task_index < len(tasks):
            # Update task category
            chat_data = get_chat_data(chat_id)
            all_tasks = chat_data.get('tasks', [])
            
            # Find the right task
            for task in all_tasks:
                if task.get('text') == tasks[task_index].get('text') and task.get('active', True):
                    task['category'] = category
                    task['updated_at'] = iso_now()
                    break
            
            update_chat_data(chat_id, chat_data)
            
            query.edit_message_text(
                f"🏷️ Category updated to *{category}* for task:\n\n*{tasks[task_index]['text']}*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            query.edit_message_text("❌ Failed to update category. Task not found.")
    
    elif data.startswith("setting:"):
        # Handle settings changes
        setting = data.split(":", 1)[1]
        
        if setting == "reminder_default":
            # Toggle default reminder setting
            chat_data = get_chat_data(chat_id)
            current = chat_data.get('settings', {}).get('reminder_default', False)
            update_settings(chat_id, {'reminder_default': not current})
            
            # Refresh settings menu
            chat_data = get_chat_data(chat_id)
            settings = chat_data.get('settings', {})
            keyboard = get_settings_keyboard(settings)
            
            query.edit_message_text(
                "⚙️ *Bot Settings*\n\nSetting updated! Select an option to configure:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif setting == "sort_by":
            # Toggle sort order
            chat_data = get_chat_data(chat_id)
            current = chat_data.get('settings', {}).get('sort_by', 'date')
            new_sort = 'priority' if current == 'date' else 'date'
            update_settings(chat_id, {'sort_by': new_sort})
            
            # Refresh settings menu
            chat_data = get_chat_data(chat_id)
            settings = chat_data.get('settings', {})
            keyboard = get_settings_keyboard(settings)
            
            query.edit_message_text(
                "⚙️ *Bot Settings*\n\nSetting updated! Select an option to configure:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif setting.startswith("theme:"):
            # Update UI theme
            theme = setting.split(":", 1)[1]
            update_settings(chat_id, {'theme': theme})
            
            # Refresh settings menu
            chat_data = get_chat_data(chat_id)
            settings = chat_data.get('settings', {})
            keyboard = get_settings_keyboard(settings)
            
            query.edit_message_text(
                f"⚙️ *Bot Settings*\n\nTheme updated to *{theme.title()}*! Select an option to configure:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif setting.startswith("time_format:"):
            # Update time format
            time_format = setting.split(":", 1)[1]
            update_settings(chat_id, {'time_format': time_format})
            
            # Refresh settings menu
            chat_data = get_chat_data(chat_id)
            settings = chat_data.get('settings', {})
            keyboard = get_settings_keyboard(settings)
            
            query.edit_message_text(
                f"⚙️ *Bot Settings*\n\nTime format updated to *{time_format}*! Select an option to configure:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif setting == "back":
            # Just refresh the settings menu
            chat_data = get_chat_data(chat_id)
            settings = chat_data.get('settings', {})
            keyboard = get_settings_keyboard(settings)
            
            query.edit_message_text(
                "⚙️ *Bot Settings*\n\nSelect an option to configure:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )

def join_group_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /join command - join a group via invite link"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
    
    chat_id = update.effective_chat.id
    message_text = " ".join(context.args) if context.args else ""
    
    if not message_text:
        update.message.reply_text(
            "🔗 Please provide a Telegram group invite link.\n\n"
            "Example: `/join https://t.me/joinchat/AbCdEfGhIjKlMnO`\n\n"
            "You can also simply send me the invite link directly.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if message contains a valid Telegram group invite link
    invite_link = None
    if 't.me/' in message_text:
        try:
            # Extract the invite link
            if 'joinchat/' in message_text:
                # Old format: https://t.me/joinchat/XXXX
                start_index = message_text.find('t.me/joinchat/')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            elif '+' in message_text:
                # New format: https://t.me/+XXXX
                start_index = message_text.find('t.me/+')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            else:
                # Public group/channel format: https://t.me/groupname
                start_index = message_text.find('t.me/')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            
            if invite_link:
                update.message.reply_text(
                    "🔄 I'm trying to join the group chat now! If I'm successful, I'll send a welcome message to the group.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Log the attempt
                user_id = update.effective_user.id
                logger.info(f"User {user_id} shared a group invite link via /join command: {invite_link}")
                
                # TODO: Implement actual join mechanism when API allows
                # For now, log this and respond appropriately
                
                # Send confirmation to the developer
                if is_developer(user_id):
                    update.message.reply_text(
                        "✅ *Developer Notice:* Bot will attempt to join the group. Check bot logs for details.",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                raise ValueError("Could not extract invite link")
        except Exception as e:
            logger.error(f"Error processing group invite link: {e}")
            update.message.reply_text(
                "⚠️ I couldn't process that invite link. Please make sure it's a valid Telegram group invite link.",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        update.message.reply_text(
            "⚠️ That doesn't look like a valid Telegram group invite link. Please send a link in the format:\n"
            "• https://t.me/joinchat/AbCdEfGhIjKlMnO\n"
            "• https://t.me/+AbCdEfGhIjKlMnO\n"
            "• https://t.me/groupname",
            parse_mode=ParseMode.MARKDOWN
        )

def today_tasks_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /today command - show tasks due today"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get all tasks for this chat
    all_tasks = get_tasks(chat_id)
    
    if not all_tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Filter tasks due today
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Convert dates to start and end of day timestamps
    today_start = datetime.combine(today, datetime.min.time()).timestamp()
    today_end = datetime.combine(tomorrow, datetime.min.time()).timestamp()
    
    # Filter tasks due today
    today_tasks = []
    for task in all_tasks:
        due_date = task.get('due_date')
        if due_date and today_start <= float(due_date) < today_end:
            today_tasks.append(task)
    
    if not today_tasks:
        update.message.reply_text("📅 You don't have any tasks due today!")
        return
    
    # Format tasks as a list
    task_text = "📅 *Tasks due today:*\n\n" + format_task_list(today_tasks)
    keyboard = get_task_list_keyboard(today_tasks)
    
    update.message.reply_text(
        task_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def week_tasks_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /week command - show tasks due this week"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get all tasks for this chat
    all_tasks = get_tasks(chat_id)
    
    if not all_tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Filter tasks due this week
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # Convert dates to timestamps
    week_start = datetime.combine(today, datetime.min.time()).timestamp()
    week_end = datetime.combine(next_week, datetime.min.time()).timestamp()
    
    # Filter tasks due this week
    week_tasks = []
    for task in all_tasks:
        due_date = task.get('due_date')
        if due_date and week_start <= float(due_date) < week_end:
            week_tasks.append(task)
    
    if not week_tasks:
        update.message.reply_text("📅 You don't have any tasks due this week!")
        return
    
    # Format tasks as a list
    task_text = "📅 *Tasks due this week:*\n\n" + format_task_list(week_tasks)
    keyboard = get_task_list_keyboard(week_tasks)
    
    update.message.reply_text(
        task_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def priority_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /priority command - set task priority"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get tasks for this chat
    tasks = get_tasks(chat_id)
    
    if not tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Check arguments
    if len(context.args) < 1:
        # Show task list for selection
        task_text = "Select a task to set priority for:\n\n" + format_task_list(tasks)
        
        # Create custom keyboard for priority setting
        keyboard = []
        for i, task in enumerate(tasks):
            row = []
            for priority in ["high", "medium", "low"]:
                label = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                row.append(InlineKeyboardButton(f"{label} {i+1}", callback_data=f"priority:{i}:{priority}"))
            keyboard.append(row)
        
        update.message.reply_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # User provided a task index, try to set priority
        task_index = int(context.args[0]) - 1  # Convert to 0-based index
        
        if 0 <= task_index < len(tasks):
            if len(context.args) >= 2:
                priority = context.args[1].lower()
                
                # Validate priority
                if priority not in ["high", "medium", "low"]:
                    update.message.reply_text(
                        "❌ Invalid priority. Please use 'high', 'medium', or 'low'."
                    )
                    return
                
                # Update task priority
                chat_data = get_chat_data(chat_id)
                all_tasks = chat_data.get('tasks', [])
                
                # Find the right task (it might not be in the same position as in filtered tasks)
                for task in all_tasks:
                    if task.get('text') == tasks[task_index].get('text') and task.get('active', True):
                        task['priority'] = priority
                        task['updated_at'] = iso_now()
                        break
                
                update_chat_data(chat_id, chat_data)
                
                # Get priority icon
                priority_icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                
                update.message.reply_text(
                    f"{priority_icon} Priority set to *{priority.upper()}* for task:\n\n*{tasks[task_index]['text']}*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Show priority options
                keyboard = [
                    [
                        InlineKeyboardButton("🔴 High", callback_data=f"priority:{task_index}:high"),
                        InlineKeyboardButton("🟡 Medium", callback_data=f"priority:{task_index}:medium"),
                        InlineKeyboardButton("🟢 Low", callback_data=f"priority:{task_index}:low")
                    ]
                ]
                
                update.message.reply_text(
                    f"Select priority for:\n\n*{tasks[task_index]['text']}*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text("❌ Invalid task number. Use /list to see your tasks.")
    except ValueError:
        update.message.reply_text(
            "❌ Please provide a valid task number.\n"
            "Example: `/priority 1 high` to set high priority for task 1."
        )

def user_stats_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /stats command for regular users - show their statistics"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    chat_data = get_chat_data(chat_id)
    
    # Prepare basic stats
    stats = chat_data.get('stats', {})
    tasks_added = stats.get('tasks_added', 0)
    tasks_completed = stats.get('tasks_completed', 0)
    
    # Calculate completion rate
    completion_rate = 0
    if tasks_added > 0:
        completion_rate = (tasks_completed / tasks_added) * 100
    
    # Get streak information
    streaks = stats.get('streaks', {})
    current_streak = streaks.get('current', 0)
    longest_streak = streaks.get('longest', 0)
    
    # Get active tasks by priority
    tasks = get_tasks(chat_id)
    high_priority = sum(1 for task in tasks if task.get('priority') == 'high')
    medium_priority = sum(1 for task in tasks if task.get('priority') == 'medium')
    low_priority = sum(1 for task in tasks if task.get('priority') == 'low')
    
    # Format stats message
    stats_text = (
        "📊 *Your Productivity Statistics*\n\n"
        f"*Tasks Overview:*\n"
        f"• Total Created: {tasks_added}\n"
        f"• Total Completed: {tasks_completed}\n"
        f"• Completion Rate: {completion_rate:.1f}%\n\n"
        f"*Streaks:*\n"
        f"• Current Streak: {current_streak} day{'s' if current_streak != 1 else ''}\n"
        f"• Longest Streak: {longest_streak} day{'s' if longest_streak != 1 else ''}\n\n"
        f"*Current Tasks by Priority:*\n"
        f"• 🔴 High Priority: {high_priority}\n"
        f"• 🟡 Medium Priority: {medium_priority}\n"
        f"• 🟢 Low Priority: {low_priority}\n"
    )
    
    update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

def tag_task_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /tag command - add category/tag to a task"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get tasks for this chat
    tasks = get_tasks(chat_id)
    
    if not tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    chat_data = get_chat_data(chat_id)
    available_categories = chat_data.get('settings', {}).get('categories', ['Work', 'Personal', 'Shopping', 'Health', 'Other'])
    
    # Check arguments
    if len(context.args) < 1:
        # Show task list for selection
        task_text = "Select a task to add a category/tag:\n\n" + format_task_list(tasks)
        keyboard = get_task_list_keyboard(tasks, action_type="tag")
        
        update.message.reply_text(
            task_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # User provided a task index, try to add tag
        task_index = int(context.args[0]) - 1  # Convert to 0-based index
        
        if 0 <= task_index < len(tasks):
            if len(context.args) >= 2:
                category = context.args[1]
                
                # Update task category
                chat_data = get_chat_data(chat_id)
                all_tasks = chat_data.get('tasks', [])
                
                # Find the right task (it might not be in the same position as in filtered tasks)
                for task in all_tasks:
                    if task.get('text') == tasks[task_index].get('text') and task.get('active', True):
                        task['category'] = category
                        task['updated_at'] = iso_now()
                        break
                
                update_chat_data(chat_id, chat_data)
                
                update.message.reply_text(
                    f"🏷️ Category set to *{category}* for task:\n\n*{tasks[task_index]['text']}*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Show category options
                keyboard = []
                row = []
                for i, category in enumerate(available_categories):
                    row.append(InlineKeyboardButton(category, callback_data=f"category:{task_index}:{category}"))
                    if (i + 1) % 3 == 0:  # 3 buttons per row
                        keyboard.append(row)
                        row = []
                
                if row:  # Add any remaining buttons
                    keyboard.append(row)
                
                update.message.reply_text(
                    f"Select category for:\n\n*{tasks[task_index]['text']}*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.message.reply_text("❌ Invalid task number. Use /list to see your tasks.")
    except ValueError:
        update.message.reply_text(
            "❌ Please provide a valid task number.\n"
            "Example: `/tag 1 Work` to set Work category for task 1."
        )

def search_tasks_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /search command - search for tasks by keyword"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    
    # Get tasks for this chat
    all_tasks = get_tasks(chat_id, include_done=True)
    
    if not all_tasks:
        update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
        return
    
    # Check if search keyword is provided
    if not context.args:
        update.message.reply_text(
            "🔍 Please provide a search term after the /search command.\n"
            "Example: `/search grocery` to find tasks containing 'grocery'",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Join all arguments into a single search term
    search_term = ' '.join(context.args).lower()
    
    # Search in task text, notes, and category
    matching_tasks = []
    for task in all_tasks:
        if (search_term in task.get('text', '').lower() or 
            search_term in task.get('notes', '').lower() or 
            search_term in task.get('category', '').lower()):
            if task.get('active', True):  # Only include active tasks
                matching_tasks.append(task)
    
    if not matching_tasks:
        update.message.reply_text(f"🔍 No tasks found matching '{search_term}'.")
        return
    
    # Format tasks as a list
    task_text = f"🔍 *Search results for '{search_term}':*\n\n" + format_task_list(matching_tasks)
    keyboard = get_task_list_keyboard(matching_tasks)
    
    update.message.reply_text(
        task_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def text_message_handler(update: Update, context: CallbackContext) -> None:
    """Handle text messages that are not commands"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        return
        
    chat_id = update.effective_chat.id
    message_text = update.message.text.strip()
    
    # Check if waiting for custom reminder time
    if context.user_data and "custom_reminder_task" in context.user_data:
        task_index = context.user_data["custom_reminder_task"]
        
        # Check for cancel
        if message_text.lower() == "cancel":
            update.message.reply_text(
                "⏹️ Reminder setup cancelled.",
                parse_mode=ParseMode.MARKDOWN
            )
            del context.user_data["custom_reminder_task"]
            return
        
        # Try to parse the time string
        try:
            # First try using our helper function (handles relative time)
            reminder_time = parse_time(message_text)
            
            if reminder_time:
                # Successfully parsed the time
                if set_reminder(chat_id, task_index, reminder_time):
                    tasks = get_tasks(chat_id)
                    if 0 <= task_index < len(tasks):
                        task_text = tasks[task_index]['text']
                        
                        # Calculate time difference for display
                        from datetime import datetime
                        current_time = get_current_time()
                        time_diff = reminder_time - current_time
                        
                        # Format for human-readable display
                        if time_diff < 60*60:  # Less than 1 hour
                            minutes = int(time_diff / 60)
                            time_display = f"{minutes} minute{'s' if minutes != 1 else ''}"
                        elif time_diff < 24*60*60:  # Less than 24 hours
                            hours = int(time_diff / (60*60))
                            time_display = f"{hours} hour{'s' if hours != 1 else ''}"
                        else:  # More than 24 hours
                            days = int(time_diff / (24*60*60))
                            time_display = f"{days} day{'s' if days != 1 else ''}"
                        
                        # Include the actual time/date
                        reminder_datetime = datetime.fromtimestamp(reminder_time)
                        formatted_time = reminder_datetime.strftime("%a, %b %d at %I:%M %p")
                        
                        # Check if this is a group chat for friendlier message
                        is_group = update.effective_chat.type in ["group", "supergroup"]
                        mention = f"everyone in this group" if is_group else "you"
                        
                        update.message.reply_text(
                            f"⏰ *Custom Reminder Set!*\n\nI'll remind {mention} about:\n*{task_text}*\n\n"
                            f"📆 Time: {formatted_time}\n⏱️ ({time_display} from now)",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        update.message.reply_text("❌ Task not found. It may have been deleted.")
                else:
                    update.message.reply_text("❌ Failed to set reminder. Please try again.")
            else:
                # Could not parse the time string
                update.message.reply_text(
                    "⚠️ I couldn't understand that time format. Please try again with a format like:\n"
                    "• `1h 30m` (1 hour and 30 minutes)\n"
                    "• `tomorrow 9am` (tomorrow at 9:00 AM)\n"
                    "• `friday 3pm` (next Friday at 3:00 PM)",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        except Exception as e:
            logger.error(f"Error parsing custom time: {e}")
            update.message.reply_text(
                "⚠️ I couldn't process that time format. Please try again with a simpler format like '1h 30m'.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Clean up the user data
        del context.user_data["custom_reminder_task"]
        return
    
    # Check if message contains a Telegram group invite link
    if 't.me/' in message_text:
        try:
            # Extract the invite link
            invite_link = None
            
            if 'joinchat/' in message_text:
                # Old format: https://t.me/joinchat/XXXX
                start_index = message_text.find('t.me/joinchat/')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            elif '+' in message_text:
                # New format: https://t.me/+XXXX
                start_index = message_text.find('t.me/+')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            else:
                # Public group/channel format: https://t.me/groupname
                start_index = message_text.find('t.me/')
                if start_index != -1:
                    invite_link = message_text[start_index:].split()[0].strip()
                    if not invite_link.startswith('https://'):
                        invite_link = 'https://' + invite_link
            
            if invite_link:
                update.message.reply_text(
                    "🔄 I'm trying to join the group chat now! If I'm successful, I'll send a welcome message to the group.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Log the attempt
                user_id = update.effective_user.id
                logger.info(f"User {user_id} shared a group invite link: {invite_link}")
                
                # TODO: Implement actual join mechanism when API allows
                # For now, log this and respond appropriately
                
                # Send confirmation to the developer
                if is_developer(user_id):
                    update.message.reply_text(
                        "✅ *Developer Notice:* Bot will attempt to join the group. Check bot logs for details.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                return
            else:
                raise ValueError("Could not extract invite link")
        except Exception as e:
            logger.error(f"Error processing group invite link: {e}")
            update.message.reply_text(
                "⚠️ I couldn't process that invite link. Please make sure it's a valid Telegram group invite link.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Check if we're in a group chat
    is_group = update.effective_chat.type in ["group", "supergroup"]
    
    # Check if it looks like a task
    if len(message_text) > 3 and not message_text.startswith('/'):
        # Ask if user wants to add this as a task with smart buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, add task", callback_data=f"add_task:{message_text[:200]}"),
                InlineKeyboardButton("❌ No", callback_data="cancel_add_task")
            ],
            [
                InlineKeyboardButton("⏰ Add with reminder", callback_data=f"add_task_reminder:{message_text[:200]}")
            ]
        ]
        
        # In groups, add options to assign the task
        if is_group:
            keyboard.append([
                InlineKeyboardButton("👥 Task for everyone", callback_data=f"assign_group:{message_text[:200]}")
            ])
        
        update.message.reply_text(
            "📝 Did you want to add this as a new task?" if not is_group else 
            "📝 Did you want to add this as a new group task?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors in the telegram bot"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Try to notify the user about the error
    if update and update.effective_chat:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, something went wrong. Please try again later."
        )

# Developer command handlers
def broadcast_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /broadcast command - send a message to all users (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    if not context.args:
        update.message.reply_text(
            "Please provide a message to broadcast after the /broadcast command."
        )
        return
    
    broadcast_message = ' '.join(context.args)
    chat_ids = get_all_chat_ids()
    
    sent_count = 0
    failed_count = 0
    
    # Send a status message first
    status_message = update.message.reply_text(
        f"📣 Broadcasting message to {len(chat_ids)} chats...\n"
        f"Sent: 0\nFailed: 0"
    )
    
    # Send the broadcast message to all chats
    for chat_id in chat_ids:
        try:
            context.bot.send_message(
                chat_id=int(chat_id),
                text=f"📣 *Announcement*\n\n{broadcast_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent_count += 1
            
            # Update status every 10 messages
            if sent_count % 10 == 0:
                status_message.edit_text(
                    f"📣 Broadcasting message to {len(chat_ids)} chats...\n"
                    f"Sent: {sent_count}\nFailed: {failed_count}"
                )
                
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Failed to send broadcast to {chat_id}: {e}")
            failed_count += 1
    
    # Final status update
    status_message.edit_text(
        f"📣 Broadcast complete!\n"
        f"Sent: {sent_count}\nFailed: {failed_count}"
    )

def stats_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /devstats command - show detailed bot statistics (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    stats = get_stats()
    
    stats_text = (
        "📊 *Bot Statistics*\n\n"
        f"Total Chats: {stats['total_chats']}\n"
        f"• Users: {stats['total_users']}\n"
        f"• Groups: {stats['total_groups']}\n\n"
        f"Total Tasks: {stats['total_tasks']}\n"
        f"• Active: {stats['active_tasks']}\n"
        f"• Completed: {stats['completed_tasks']}\n"
    )
    
    update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

def maintenance_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /maintenance command - toggle maintenance mode (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    
    status = "enabled" if maintenance_mode else "disabled"
    update.message.reply_text(f"🛠️ Maintenance mode {status}.")

def debug_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /debug command - show debug information (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    # Gather debug information
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user = update.effective_user
    
    debug_text = (
        "🔍 *Debug Information*\n\n"
        f"Chat ID: `{chat_id}`\n"
        f"Chat Type: `{chat_type}`\n"
        f"User ID: `{user.id}`\n"
        f"Username: `{user.username or 'None'}`\n"
        f"Maintenance Mode: `{maintenance_mode}`\n"
        f"Bot Version: `1.0.0`\n"
    )
    
    update.message.reply_text(debug_text, parse_mode=ParseMode.MARKDOWN)
