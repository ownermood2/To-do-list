import logging
import time
from telegram import Update, InlineKeyboardMarkup, ParseMode
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
    get_stats
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
    if data.startswith("done:"):
        # Mark task as done
        task_index = int(data.split(":")[1])
        if mark_task_done(chat_id, task_index):
            tasks = get_tasks(chat_id, include_done=True)
            task_text = tasks[task_index]['text']
            
            # Update the message to reflect the change
            query.edit_message_text(
                f"✅ Task marked as done: *{task_text}*",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("delete:"):
        # Delete task (after confirmation)
        task_index = int(data.split(":")[1])
        tasks = get_tasks(chat_id)
        
        if 0 <= task_index < len(tasks):
            task_text = tasks[task_index]['text']
            
            if delete_task(chat_id, task_index):
                query.edit_message_text(
                    f"🗑️ Task deleted: *{task_text}*",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                query.edit_message_text("❌ Failed to delete task. Please try again.")
    
    elif data == "confirm_delete":
        # Extract task index from original message
        original_text = query.message.text
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
            
            query.edit_message_text(
                f"Select when to be reminded about:\n\n*{task_text}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
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
                
                query.edit_message_text(
                    f"⏰ Reminder set for *{task_text}* in {time_display}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                query.edit_message_text("❌ Task not found. It may have been deleted.")
        else:
            query.edit_message_text("❌ Failed to set reminder. Please try again.")
    
    elif data.startswith("setting:"):
        # Handle settings changes
        setting = data.split(":")[1]
        
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

def text_message_handler(update: Update, context: CallbackContext) -> None:
    """Handle text messages that are not commands"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        return
        
    chat_id = update.effective_chat.id
    message = update.message.text
    
    # Check if this looks like a task (not implemented yet, but could detect patterns like "Remember to...")
    if len(message) <= 100 and not message.startswith('/'):
        # This could be a shorthand for adding a task
        # For now, just suggest using the /add command
        update.message.reply_text(
            f"Did you want to add this as a task? Use:\n`/add {message}`",
            parse_mode=ParseMode.MARKDOWN
        )

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
    """Handle the /stats command - show bot statistics (developer only)"""
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
