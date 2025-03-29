import logging
import time
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext
from telegram.error import BadRequest, Unauthorized, TimedOut, NetworkError

# Chat type constants for better code readability
CHAT_TYPE_PRIVATE = "private"
CHAT_TYPE_GROUP = "group"
CHAT_TYPE_SUPERGROUP = "supergroup"
CHAT_TYPE_CHANNEL = "channel"
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
from utils import (
    is_developer,
    add_developer,
    format_task_list,
    parse_time,
    format_task_details,
    get_current_time
)

from keyboards import (
    get_task_list_keyboard,
    get_settings_keyboard,
    get_confirmation_keyboard,
    get_time_selection_keyboard
)


logger = logging.getLogger(__name__)

# Global maintenance mode flag
maintenance_mode = False

# Using the chat types constants defined above

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
    task_index = len(get_tasks(chat_id)) - 1  # Get index of newly added task
    
    # Get chat type to personalize the message
    chat_type = update.effective_chat.type
    is_group = chat_type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
    
    # Create task added confirmation message
    success_message = (
        f"✅ Task added successfully!\n\n*{task_text}*\n\n"
        "Would you like to set a reminder for this task?"
    )
    
    # Set up reminder keyboard for the task
    keyboard = get_time_selection_keyboard(task_index)
    
    update.message.reply_text(
        success_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
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
    
    # Import chat types
    from config import CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP
    user_id = update.callback_query.from_user.id
    
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
        is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
        
        query.edit_message_text(
            f"⏰ Task added! When should I remind {'everyone' if is_group else 'you'} about:\n\n*{task_text}*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("assign_group:"):
        # Add a task specifically for the group (everyone)
        task_text = data.split(":", 1)[1]
        
        # Check if we're actually in a group chat
        is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
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
            is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
            
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
        
    # Chat cleanup actions
    elif data.startswith("clean_chat:"):
        action = data.split(":", 1)[1]
        chat_type = update.effective_chat.type
        
        if action == "bot_only":
            # Try to clean up recent bot messages
            try:
                # Delete the prompt message
                query.message.delete()
                
                # Show temporary confirmation message that will self-destruct
                cleanup_msg = context.bot.send_message(
                    chat_id=chat_id,
                    text="🧹 *Cleaning up my messages...*\n(This message will disappear in a few seconds)",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Schedule this message for deletion too
                context.job_queue.run_once(
                    lambda job_context: cleanup_msg.delete(),
                    5,  # 5 seconds delay
                    context=None
                )
                
                # If we have a record of recent bot messages in this chat, try to delete them
                if context.chat_data.get('cleanup_messages'):
                    for msg_data in context.chat_data['cleanup_messages']:
                        try:
                            # Try to delete both command and prompt messages
                            context.bot.delete_message(chat_id=chat_id, message_id=msg_data['command_id'])
                            context.bot.delete_message(chat_id=chat_id, message_id=msg_data['prompt_id'])
                        except Exception as e:
                            logger.debug(f"Could not delete message {msg_data['prompt_id']}: {e}")
                    
                    # Clear the cleanup messages list
                    context.chat_data['cleanup_messages'] = []
                
                logger.info(f"Chat cleanup (bot messages) executed in {chat_id}")
                
            except Exception as e:
                logger.error(f"Error during chat cleanup: {e}")
                # Don't send error message to avoid adding more clutter
        
        elif action == "tasks":
            # In group chats, offer to clean all task listings
            if chat_type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]:
                # Show a confirmation keyboard first
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Yes, clean all", callback_data="confirm_clear"),
                        InlineKeyboardButton("❌ No, cancel", callback_data="cancel_clear")
                    ]
                ]
                
                query.edit_message_text(
                    "⚠️ *Are you sure?*\n\nThis will clear ALL tasks for this group. This action cannot be undone.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            else:
                # For private chats, do the same
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Yes, clean all", callback_data="confirm_clear"),
                        InlineKeyboardButton("❌ No, cancel", callback_data="cancel_clear")
                    ]
                ]
                
                query.edit_message_text(
                    "⚠️ *Are you sure?*\n\nThis will clear ALL your tasks. This action cannot be undone.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        elif action == "completed":
            # Only for private chats, clear completed tasks
            # First offer confirmation
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, clear completed", callback_data="confirm_clear_completed"),
                    InlineKeyboardButton("❌ No, cancel", callback_data="cancel_clear")
                ]
            ]
            
            query.edit_message_text(
                "⚠️ *Clear completed tasks?*\n\nThis will remove all completed tasks from your list.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif action == "cancel":
            query.edit_message_text(
                "❌ Cleanup operation cancelled.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data == "confirm_clear_completed":
        # Clear only completed tasks
        try:
            # Get all tasks for this chat
            chat_data = get_chat_data(chat_id)
            tasks = chat_data.get('tasks', [])
            
            # Count how many completed tasks we have
            completed_count = sum(1 for task in tasks if task.get('done', False))
            
            # Filter out completed tasks
            chat_data['tasks'] = [task for task in tasks if not task.get('done', False)]
            update_chat_data(chat_id, chat_data)
            
            query.edit_message_text(
                f"🧹 Cleared {completed_count} completed tasks.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error clearing completed tasks: {e}")
            query.edit_message_text(
                "❌ There was an error clearing your completed tasks. Please try again later.",
                parse_mode=ParseMode.MARKDOWN
            )
            
    # Broadcast deletion related callbacks
    elif data.startswith("delbroadcast:"):
        # Only developers can delete broadcasts
        if not is_developer(user_id):
            query.answer("⚠️ Only developers can delete broadcasts.")
            return
            
        broadcast_id = data.split(":", 1)[1]
        
        # Check if broadcast exists
        if 'broadcasts' not in context.bot_data or broadcast_id not in context.bot_data['broadcasts']:
            query.edit_message_text(f"❌ Broadcast with ID {broadcast_id} not found.")
            return
            
        broadcast = context.bot_data['broadcasts'][broadcast_id]
        sent_messages = broadcast.get('sent_messages', [])
        message_preview = broadcast['message'][:100] + "..." if len(broadcast['message']) > 100 else broadcast['message']
        
        # Ask for confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, delete all", callback_data=f"confirm_delbroadcast:{broadcast_id}"),
                InlineKeyboardButton("❌ No, cancel", callback_data="cancel_delbroadcast")
            ]
        ]
        
        query.edit_message_text(
            f"🗑️ *Delete Broadcast Confirmation*\n\n"
            f"You are about to delete this broadcast from {len(sent_messages)} chats:\n\n"
            f"Message: {message_preview}\n\n"
            f"Are you sure you want to proceed?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("viewbroadcast:"):
        # Only developers can view broadcasts
        if not is_developer(user_id):
            query.answer("⚠️ Only developers can view broadcast details.")
            return
            
        broadcast_id = data.split(":", 1)[1]
        
        # Check if broadcast exists
        if 'broadcasts' not in context.bot_data or broadcast_id not in context.bot_data['broadcasts']:
            query.edit_message_text(f"❌ Broadcast with ID {broadcast_id} not found.")
            return
            
        broadcast = context.bot_data['broadcasts'][broadcast_id]
        sent_messages = broadcast.get('sent_messages', [])
        
        # Create a list of chats where the message was sent
        chat_list = ""
        for i, msg in enumerate(sent_messages[:10]):  # Show only the first 10
            try:
                chat_id = msg['chat_id']
                chat_info = context.bot.get_chat(chat_id)
                if chat_info.username:
                    chat_name = f"@{chat_info.username}"
                else:
                    chat_name = chat_info.title or f"Chat {chat_id}"
                    
                chat_list += f"• {chat_name}\n"
            except Exception:
                chat_list += f"• Chat {chat_id}\n"
                
        if len(sent_messages) > 10:
            chat_list += f"... and {len(sent_messages) - 10} more\n"
            
        if not chat_list:
            chat_list = "No chats found."
            
        # Create keyboard to go back or delete
        keyboard = [
            [
                InlineKeyboardButton("🗑️ Delete Broadcast", callback_data=f"delbroadcast:{broadcast_id}"),
                InlineKeyboardButton("◀️ Back", callback_data="back_to_broadcasts")
            ]
        ]
        
        query.edit_message_text(
            f"📢 *Broadcast Details*\n\n"
            f"🆔 ID: `{broadcast_id}`\n"
            f"⏰ Time: {broadcast.get('timestamp', 'Unknown')}\n"
            f"📨 Sent to: {len(sent_messages)} chats\n\n"
            f"📝 *Message:*\n{broadcast['message']}\n\n"
            f"📋 *Sent to chats:*\n{chat_list}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "back_to_broadcasts":
        # Go back to broadcast list
        if not is_developer(user_id):
            query.answer("⚠️ Only developers can view broadcasts.")
            return
            
        query.edit_message_text(
            "Please use /delbroadcast to see the list of recent broadcasts.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("confirm_delbroadcast:"):
        # Process broadcast deletion confirmation
        if not is_developer(user_id):
            query.answer("⚠️ Only developers can delete broadcasts.")
            return
            
        broadcast_id = data.split(":", 1)[1]
        
        # Check if broadcast exists
        if 'broadcasts' not in context.bot_data or broadcast_id not in context.bot_data['broadcasts']:
            query.edit_message_text(f"❌ Broadcast with ID {broadcast_id} not found.")
            return
            
        broadcast = context.bot_data['broadcasts'][broadcast_id]
        sent_messages = broadcast.get('sent_messages', [])
        
        # Send a status message first
        query.edit_message_text(
            f"🗑️ Deleting broadcast messages from {len(sent_messages)} chats...\n"
            f"Deleted: 0\nFailed: 0",
            parse_mode=ParseMode.MARKDOWN
        )
        
        deleted_count = 0
        failed_count = 0
        
        # Delete each message
        for msg in sent_messages:
            try:
                context.bot.delete_message(
                    chat_id=msg['chat_id'],
                    message_id=msg['message_id']
                )
                deleted_count += 1
                
                # Update status every 10 deletions
                if deleted_count % 10 == 0:
                    query.edit_message_text(
                        f"🗑️ Deleting broadcast messages from {len(sent_messages)} chats...\n"
                        f"Deleted: {deleted_count}\nFailed: {failed_count}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to delete message from {msg['chat_id']}: {e}")
                failed_count += 1
        
        # Remove the broadcast from bot_data
        del context.bot_data['broadcasts'][broadcast_id]
        
        # Final status update
        query.edit_message_text(
            f"🗑️ Broadcast deletion complete!\n"
            f"Deleted: {deleted_count}\nFailed: {failed_count}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "cancel_delbroadcast":
        # User cancelled broadcast deletion
        query.edit_message_text(
            "⏹️ Broadcast deletion cancelled.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "group_help":
        # Display helpful information for groups
        group_commands = [
            "*/add* - Create a new task for the group",
            "*/list* - View all active group tasks",
            "*/done* - Mark a task as completed",
            "*/delete* - Remove a task from the list",
            "*/remind* - Set a reminder for a task",
            "*/today* - View tasks due today",
            "*/priority* - Set task priority (high/medium/low)",
            "*/tag* - Add a category to a task",
            "*/clean* - Clean up bot messages in the chat"
        ]
        
        # Create a help message with basic commands
        help_text = "📚 *Group Commands*\n\n" + "\n".join(group_commands) + "\n\n"
        help_text += "To mention the entire group in reminders, use `/remind` with any task."
        
        # Add a keyboard with the most useful commands
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Task", callback_data="show_add_format"),
                InlineKeyboardButton("📋 List Tasks", callback_data="show_list_format")
            ],
            [
                InlineKeyboardButton("⏰ Set Reminder", callback_data="show_remind_format"),
                InlineKeyboardButton("🧹 Clean Chat", callback_data="show_clean_format")
            ]
        ]
        
        query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "show_add_format":
        # Show the format for adding tasks
        query.edit_message_text(
            "➕ *Adding Tasks*\n\n"
            "Use `/add` followed by your task description:\n"
            "`/add Buy snacks for the meeting`\n\n"
            "You can also add tasks with due dates:\n"
            "`/add Submit report due:friday`\n\n"
            "Or with priorities:\n"
            "`/add Call client priority:high`",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "show_list_format":
        # Show the format for listing tasks
        query.edit_message_text(
            "📋 *Listing Tasks*\n\n"
            "Use `/list` to view all active tasks\n"
            "Use `/today` to see tasks due today\n"
            "Use `/list done` to see completed tasks\n\n"
            "From the list view, you can mark tasks as done, delete them, or set reminders with the inline buttons.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "show_remind_format":
        # Show the format for setting reminders
        query.edit_message_text(
            "⏰ *Setting Reminders*\n\n"
            "Use `/remind` followed by the task number and time:\n"
            "`/remind 1 30m` (30 minutes)\n"
            "`/remind 2 2h` (2 hours)\n"
            "`/remind 3 tomorrow 9am`\n\n"
            "Or use `/list` and click the ⏰ button next to any task.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data == "show_clean_format":
        # Show the format for cleaning chat
        query.edit_message_text(
            "🧹 *Cleaning Chat*\n\n"
            "Use `/clean` to remove bot messages and keep the chat tidy.\n\n"
            "Options:\n"
            "• Clean bot messages: Removes recent bot responses\n"
            "• Clean all tasks: Clears the task list (requires confirmation)\n\n"
            "This helps keep your group chat organized and focused.",
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
                is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
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
                is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
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
                # Send initial response to the user
                response_msg = update.message.reply_text(
                    "🔄 I'm trying to join the group chat now! If I'm successful, I'll send a welcome message to the group.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Log the attempt
                user_id = update.effective_user.id
                logger.info(f"User {user_id} shared a group invite link via /join command: {invite_link}")
                
                # Actually try to join the group
                try:
                    # Extract chat username or invite link for joining
                    if 't.me/' in invite_link and not ('joinchat' in invite_link or '+' in invite_link):
                        # For public groups: get the username after t.me/
                        username_part = invite_link.split('t.me/')[-1].strip()
                        
                        # If username has additional path or query parameters, remove them
                        if '/' in username_part:
                            username_part = username_part.split('/')[0]
                        if '?' in username_part:
                            username_part = username_part.split('?')[0]
                        
                        # Add @ prefix if not already present
                        if not username_part.startswith('@'):
                            username_part = '@' + username_part
                        
                        # Try to join by username
                        result = context.bot.get_chat(username_part)
                        new_chat_id = result.id
                        chat_title = result.title
                        
                        # Send welcome message
                        context.bot.send_message(
                            chat_id=new_chat_id,
                            text=(
                                "👋 *Hello everyone!*\n\n"
                                "I'm *TaskMaster Pro*, a task management bot that can help this group organize tasks "
                                "and send reminders. Use /help to see what I can do!\n\n"
                                "I was invited to this group by a user. If you'd like to get started, "
                                "just type /start to activate me in this group."
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Update the user who invited the bot
                        update.message.reply_text(
                            f"✅ I've successfully joined the group *{chat_title}*! I've sent a welcome message to introduce myself.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logger.info(f"Bot successfully joined group {chat_title} (ID: {new_chat_id}) via username")
                        
                    else:
                        # For private groups, use the invite link directly
                        chat = context.bot.join_chat(invite_link)
                        new_chat_id = chat.id
                        chat_title = chat.title
                        
                        # Send welcome message
                        context.bot.send_message(
                            chat_id=new_chat_id,
                            text=(
                                "👋 *Hello everyone!*\n\n"
                                "I'm *TaskMaster Pro*, a task management bot that can help this group organize tasks "
                                "and send reminders. Use /help to see what I can do!\n\n"
                                "I was invited to this group by a user. If you'd like to get started, "
                                "just type /start to activate me in this group."
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Update the user who invited the bot
                        update.message.reply_text(
                            f"✅ I've successfully joined the group *{chat_title}*! I've sent a welcome message to introduce myself.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logger.info(f"Bot successfully joined group {chat_title} (ID: {new_chat_id}) via invite link")
                    
                except BadRequest as e:
                    error_msg = str(e).lower()
                    if "chat not found" in error_msg:
                        update.message.reply_text(
                            "❌ I couldn't find that group. The link may be invalid or the group may no longer exist.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif "not enough rights" in error_msg or "insufficient rights" in error_msg:
                        update.message.reply_text(
                            "❌ I don't have sufficient permissions to join this group. Please ensure I have the right to join groups via invite links.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif "bot was blocked" in error_msg or "bot was kicked" in error_msg:
                        update.message.reply_text(
                            "❌ I've been blocked or kicked from this group previously. I cannot join it again unless an admin unblocks me.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif "invite link has expired" in error_msg or "invite link is invalid" in error_msg:
                        update.message.reply_text(
                            "❌ This invite link has expired or is invalid. Please get a fresh invite link and try again.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        update.message.reply_text(
                            f"❌ Error joining group: {e}\n\nPlease try again with a valid invite link or check if I have permission to join.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    logger.error(f"Failed to join group via link {invite_link}: {e}")
                
                except Exception as e:
                    update.message.reply_text(
                        "❌ An unexpected error occurred while trying to join the group. Please try again later.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    logger.error(f"Unexpected error joining group via link {invite_link}: {e}")
                
                # Send detailed info to developers
                if is_developer(user_id):
                    update.message.reply_text(
                        "✅ *Developer Notice:* Bot has attempted to join the group. Check bot logs for details.",
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

def clean_chat_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /clean command - clean up bot messages from chat"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        update.message.reply_text("🛠️ Bot is currently in maintenance mode. Please try again later.")
        return
        
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Store the message ID to refer back after confirmation
    command_message_id = update.message.message_id
    
    # We need different approaches for groups vs private chats
    if chat_type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]:
        # For groups, offer options with confirmation
        keyboard = [
            [
                InlineKeyboardButton("🧹 Clean bot messages", callback_data="clean_chat:bot_only"),
                InlineKeyboardButton("🧹 Clean all tasks", callback_data="clean_chat:tasks")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="clean_chat:cancel")
            ]
        ]
        
        prompt_message = update.message.reply_text(
            "🧹 *Chat Cleanup Options*\n\n"
            "• *Clean bot messages*: Removes recent bot messages from this chat\n"
            "• *Clean all tasks*: Removes task listings and prompts\n\n"
            "What would you like to do?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Store the prompt message ID in the context for later deletion
        if not context.chat_data.get('cleanup_messages'):
            context.chat_data['cleanup_messages'] = []
        
        context.chat_data['cleanup_messages'].append({
            'command_id': command_message_id,
            'prompt_id': prompt_message.message_id,
            'timestamp': datetime.now().timestamp()
        })
        
        # Schedule automatic cleanup of old cleanup messages
        def clean_old_prompts(context):
            if context.chat_data.get('cleanup_messages'):
                current_time = datetime.now().timestamp()
                # Filter out messages older than 10 minutes
                context.chat_data['cleanup_messages'] = [
                    msg for msg in context.chat_data['cleanup_messages'] 
                    if current_time - msg['timestamp'] < 600  # 10 minutes
                ]
        
        context.job_queue.run_once(
            clean_old_prompts,
            600,  # 10 minutes
            context=context
        )
        
        logger.info(f"Chat cleanup options presented in {chat_id} (group chat)")
    else:
        # For private chats, offer more options
        keyboard = [
            [
                InlineKeyboardButton("🧹 Clean bot messages", callback_data="clean_chat:bot_only"),
                InlineKeyboardButton("🧹 Clear completed tasks", callback_data="clean_chat:completed")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="clean_chat:cancel")
            ]
        ]
        
        update.message.reply_text(
            "🧹 *Chat Cleanup Options*\n\n"
            "• *Clean bot messages*: I'll try to remove my recent messages\n"
            "• *Clear completed tasks*: Remove all completed tasks from your list\n\n"
            "Alternatively, you can use Telegram's built-in 'Clear chat' option by clicking the three dots ⋮ in the top-right corner.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Chat cleanup options presented in {chat_id} (private chat)")

def text_message_handler(update: Update, context: CallbackContext) -> None:
    """Handle text messages that are not commands"""
    if maintenance_mode and not is_developer(update.effective_user.id):
        return
        
    chat_id = update.effective_chat.id
    
    # Handle both regular messages and edited messages
    message = update.message or update.edited_message
    if not message or not hasattr(message, 'text') or not message.text:
        # Skip processing if there's no text in the message
        return
        
    message_text = message.text.strip()
    
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
                        is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
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
    is_group = update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]
    
    # Check if this is a command with a bot username in a group chat (e.g., /done@BotUsername)
    if is_group and '@' in message_text and message_text.startswith('/'):
        try:
            # Extract the command part (e.g., "/done" from "/done@BotUsername")
            command_parts = message_text.split('@', 1)
            command = command_parts[0].strip()
            
            # Get our bot's username to check if the command is for us
            bot_username = context.bot.username
            
            # Check if the message has our bot's username
            if len(command_parts) > 1 and bot_username and command_parts[1].strip().lower() == bot_username.lower():
                logger.debug(f"Detected command for this bot in group: {command}")
                # Special handling for problematic commands
                if command == '/done':
                    # Create a new context with fixed args
                    if len(context.args) > 0:
                        # Pass through existing arguments
                        done_task_handler(update, context)
                    else:
                        # Show the task list with done buttons
                        tasks = get_tasks(chat_id)
                        if tasks:
                            task_text = "Select a task to mark as done:\n\n" + format_task_list(tasks)
                            keyboard = get_task_list_keyboard(tasks, action_type="done")
                            update.message.reply_text(
                                task_text,
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode=ParseMode.MARKDOWN
                            )
                        else:
                            update.message.reply_text("📝 You don't have any tasks yet. Use /add to create one!")
                    return
                elif command == '/priority':
                    # Special handling for priority command
                    priority_task_handler(update, context)
                    return
                elif command == '/tag':
                    # Special handling for tag command
                    tag_task_handler(update, context)
                    return
                elif command == '/delete':
                    # Special handling for delete command
                    delete_task_handler(update, context)
                    return
                # You can add more commands that need special handling here
                
        except Exception as e:
            logger.error(f"Error processing command with username: {e}")
    
    # Only prompt for task creation in private chats, not in groups
    # In groups, users must use explicit commands like /add to create tasks
    if not is_group and len(message_text) > 3 and not message_text.startswith('/'):
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
        
        update.message.reply_text(
            "📝 Did you want to add this as a new task?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    elif is_group and len(message_text) > 3 and not message_text.startswith('/'):
        # In groups, we don't automatically add tasks from regular messages
        
        # Check if the bot was mentioned
        mentioned = False
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "mention":
                    mention_text = message_text[entity.offset:entity.offset+entity.length]
                    if mention_text.lower() == f"@{context.bot.username.lower()}":
                        mentioned = True
                        break
        
        if mentioned:
            # Bot was mentioned, provide helpful information
            keyboard = [
                [
                    InlineKeyboardButton("📚 View Commands", callback_data="group_help"),
                    InlineKeyboardButton("➕ Add Task", callback_data=f"add_task:{message_text[:200]}")
                ]
            ]
            
            update.message.reply_text(
                "👋 Hi! I'm TaskMaster Pro, your task management assistant.\n\n"
                "To add a task, use `/add Task description` or click the Add Task button below.\n"
                "To see all commands, use `/help` or click View Commands.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # We don't respond to regular messages that don't mention the bot
        return

def get_message(update: Update):
    """Get the appropriate message object (regular or edited) from an update"""
    return update.message or update.edited_message

def reply_to_message(update: Update, text: str, **kwargs):
    """Helper function to reply to either normal or edited messages"""
    message = get_message(update)
    if message:
        try:
            return message.reply_text(text, **kwargs)
        except Exception as e:
            # If replying to edited message fails, try to send a new message
            logger.error(f"Error replying to message: {e}")
            if update.effective_chat:
                return update.effective_chat.send_message(text, **kwargs)
    elif update.effective_chat:
        # Fallback if no valid message
        return update.effective_chat.send_message(text, **kwargs)
    return None

def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors in the telegram bot"""
    error_message = str(context.error)
    logger.error(f"Update {update} caused error {error_message}")
    
    # Handle NoneType errors with edited_message or missing text
    if "'NoneType' object has no attribute" in error_message:
        # This is likely due to edited messages or similar, just log and ignore
        return
    
    # Skip sending error messages for entity parsing errors in groups
    if "Can't parse entities" in error_message and update and update.effective_chat:
        if update.effective_chat.type in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]:
            # Just log the error but don't send a message to avoid spamming the group
            return
    
    # For message-specific errors, we'll try to extract the command and execute it properly
    if "Can't parse entities" in error_message and update and update.effective_message:
        try:
            # Try to extract the command from the text
            message_text = update.effective_message.text
            if message_text and '@' in message_text:
                # Extract the command part before the @
                command_parts = message_text.split('@')[0].strip()
                
                # Check if this is a valid command
                if command_parts.startswith('/'):
                    # Execute the command without the bot username
                    # We'll create a new update object with the fixed command
                    logger.info(f"Attempting to process command: {command_parts}")
                    # Let the appropriate command handler handle it on the next update
                    return
        except Exception as e:
            logger.error(f"Error while trying to fix entity parsing: {e}")
    
    # Try to notify the user about the error for non-entity parsing issues
    if update and update.effective_chat:
        # Only send error messages in private chats or for non-entity parsing errors
        if update.effective_chat.type == CHAT_TYPE_PRIVATE or "Can't parse entities" not in error_message:
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
            "Please provide a message to broadcast after the /broadcast command.\n\n"
            "Usage: `/broadcast Your message`\n\n"
            "To send to a specific group, use: `/groupcast GROUP_ID Your message`"
        )
        return
    
    # Send to all users
    broadcast_message = ' '.join(context.args)
    send_global_broadcast(update, context, broadcast_message)
    
def groupcast_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /groupcast command - send a message to a specific group (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    if len(context.args) < 2:
        update.message.reply_text(
            "Please provide a group ID/username and message.\n\n"
            "Usage examples:\n"
            "• `/groupcast GROUP_ID Your message`\n"
            "• `/groupcast @group_username Your message`\n"
            "• `/groupcast group_username Your message`"
        )
        return
    
    # First argument is the group identifier (ID or username)
    group_identifier = context.args[0]
    
    # Rest is the message
    message = ' '.join(context.args[1:])
    
    # Check if it's a group ID (numeric) or username
    if group_identifier.isdigit() or (group_identifier.startswith('-') and group_identifier[1:].isdigit()):
        # It's a numeric ID
        group_id = int(group_identifier)
        send_group_broadcast_by_id(update, context, group_id, message)
    else:
        # It's a username - remove @ if present
        if group_identifier.startswith('@'):
            group_username = group_identifier[1:]
        else:
            group_username = group_identifier
            
        send_group_broadcast_by_username(update, context, group_username, message)

# Define helper functions for group broadcasts
def send_group_broadcast_by_id(update: Update, context: CallbackContext, group_id: int, message: str) -> None:
    """Send a broadcast message to a specific group by ID"""
    try:
        # First check if this is a valid group the bot knows about
        chat_ids = get_all_chat_ids()
        group_id_str = str(group_id)
        
        if group_id_str not in chat_ids:
            # Check if we can send a message to this group anyway
            try:
                # Send a test message
                context.bot.send_chat_action(chat_id=group_id, action="typing")
                chat_exists = True
            except Exception:
                chat_exists = False
                
            if not chat_exists:
                update.message.reply_text(
                    f"⚠️ Group ID {group_id} is not known to the bot or the bot cannot access the group."
                )
                return
        
        # Generate a broadcast ID for this group message
        broadcast_id = f"group_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Send the message
        success = False
        try:
            sent_msg = context.bot.send_message(
                chat_id=group_id,
                text=f"📣 *Announcement*\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            success = True
            
            # Store this broadcast in bot_data for potential deletion
            if 'broadcasts' not in context.bot_data:
                context.bot_data['broadcasts'] = {}
                
            context.bot_data['broadcasts'][broadcast_id] = {
                'message': message,
                'sent_messages': [{
                    'chat_id': group_id,
                    'message_id': sent_msg.message_id
                }],
                'timestamp': datetime.now().isoformat(),
                'sender_id': update.effective_user.id,
                'type': 'group'
            }
        except Exception as e:
            logger.error(f"Failed to send broadcast to group {group_id}: {e}")
            
        # Update status
        if success:
            update.message.reply_text(
                f"✅ Successfully sent announcement to group with ID {group_id}.\n\n"
                f"Broadcast ID: `{broadcast_id}`\n"
                f"Use /delbroadcast {broadcast_id} to delete this announcement.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text(
                f"❌ Failed to send announcement to group with ID {group_id}. Check logs for details."
            )
    
    except Exception as e:
        logger.error(f"Error in targeted broadcast: {e}")
        update.message.reply_text(
            "❌ An error occurred while trying to send the broadcast."
        )

def send_group_broadcast_by_username(update: Update, context: CallbackContext, group_username: str, message: str) -> None:
    """Send a broadcast message to a specific group by username"""
    try:
        # Attempt to send message directly to the username
        success = False
        
        # Generate a broadcast ID for this group message
        broadcast_id = f"group_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # Clean up the username if needed
            if not group_username.startswith('@'):
                chat_username = '@' + group_username
            else:
                chat_username = group_username
                
            sent_message = context.bot.send_message(
                chat_id=chat_username,
                text=f"📣 *Announcement*\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            success = True
            
            # Get the actual chat ID for reporting
            actual_chat_id = sent_message.chat_id
            
            # Store this broadcast in bot_data for potential deletion
            if 'broadcasts' not in context.bot_data:
                context.bot_data['broadcasts'] = {}
                
            context.bot_data['broadcasts'][broadcast_id] = {
                'message': message,
                'sent_messages': [{
                    'chat_id': actual_chat_id,
                    'message_id': sent_message.message_id
                }],
                'timestamp': datetime.now().isoformat(),
                'sender_id': update.effective_user.id,
                'type': 'group',
                'group_username': group_username
            }
            
        except Exception as e:
            logger.error(f"Failed to send broadcast to group @{group_username}: {e}")
            
        # Update status
        if success:
            update.message.reply_text(
                f"✅ Successfully sent announcement to group @{group_username}.\n\n"
                f"Broadcast ID: `{broadcast_id}`\n"
                f"Use /delbroadcast {broadcast_id} to delete this announcement.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text(
                f"❌ Failed to send announcement to group @{group_username}.\n"
                f"Make sure the bot is a member of this group and has permission to send messages."
            )
    
    except Exception as e:
        logger.error(f"Error in targeted broadcast: {e}")
        update.message.reply_text(
            "❌ An error occurred while trying to send the broadcast."
        )

# Keep the original function for backward compatibility
def send_group_broadcast(update: Update, context: CallbackContext, group_id: int, message: str) -> None:
    """Send a broadcast message to a specific group (legacy method)"""
    send_group_broadcast_by_id(update, context, group_id, message)

def send_global_broadcast(update: Update, context: CallbackContext, broadcast_message: str) -> None:
    """Send a broadcast message to all chats"""
    chat_ids = get_all_chat_ids()
    
    sent_count = 0
    failed_count = 0
    
    # Send a status message first
    status_message = update.message.reply_text(
        f"📣 Broadcasting message to {len(chat_ids)} chats...\n"
        f"Sent: 0\nFailed: 0"
    )
    
    # Track sent messages for potential deletion
    broadcast_id = datetime.now().strftime('%Y%m%d%H%M%S')
    sent_messages = []
    
    # Send the broadcast message to all chats
    for chat_id in chat_ids:
        try:
            # Send the message and get the message object
            sent_msg = context.bot.send_message(
                chat_id=int(chat_id),
                text=f"📣 *Announcement*\n\n{broadcast_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Store the chat ID and message ID
            sent_messages.append({
                'chat_id': int(chat_id),
                'message_id': sent_msg.message_id
            })
            
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
    
    # Save broadcast messages to bot data
    if 'broadcasts' not in context.bot_data:
        context.bot_data['broadcasts'] = {}
    
    context.bot_data['broadcasts'][broadcast_id] = {
        'message': broadcast_message,
        'sent_messages': sent_messages,
        'timestamp': datetime.now().isoformat(),
        'sender_id': update.effective_user.id
    }
    
    # Final status update with broadcast ID for deletion reference
    status_message.edit_text(
        f"📣 Broadcast complete!\n"
        f"Sent: {sent_count}\nFailed: {failed_count}\n\n"
        f"Broadcast ID: `{broadcast_id}`\n"
        f"Use /delbroadcast {broadcast_id} to delete this announcement from all chats.",
        parse_mode=ParseMode.MARKDOWN
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
    
def adddev_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /adddev command - add a new developer (developer only)"""
    # Only existing developers can add new developers
    if not is_developer(update.effective_user.id):
        update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check if user ID is provided
    if not context.args:
        update.message.reply_text(
            "Please provide a user ID to add as a developer.\n"
            "Usage: `/adddev 123456789`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Parse the user ID
        new_dev_id = int(context.args[0])
        
        # Attempt to add the user as a developer
        if add_developer(new_dev_id):
            update.message.reply_text(
                f"✅ Successfully added user {new_dev_id} as a developer.\n"
                "They now have access to all developer commands.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"User {update.effective_user.id} added {new_dev_id} as a developer")
        else:
            update.message.reply_text(
                "❌ Failed to add the user as a developer. Please check the logs."
            )
    except ValueError:
        update.message.reply_text(
            "❌ Invalid user ID format. Please provide a numeric user ID."
        )

def delete_broadcast_handler(update: Update, context: CallbackContext) -> None:
    """Handle the /delbroadcast command - delete a broadcast message from all chats (developer only)"""
    user_id = update.effective_user.id
    
    if not is_developer(user_id):
        update.message.reply_text("❌ This command is only available to developers.")
        return
    
    if not context.args:
        recent_broadcasts = []
        if 'broadcasts' in context.bot_data:
            # Get the 5 most recent broadcasts
            broadcast_ids = sorted(context.bot_data['broadcasts'].keys(), 
                                  key=lambda x: context.bot_data['broadcasts'][x].get('timestamp', ''),
                                  reverse=True)[:5]
            
            for broadcast_id in broadcast_ids:
                broadcast = context.bot_data['broadcasts'][broadcast_id]
                message_preview = broadcast['message'][:50] + "..." if len(broadcast['message']) > 50 else broadcast['message']
                sent_count = len(broadcast.get('sent_messages', []))
                timestamp = broadcast.get('timestamp', 'Unknown')
                
                try:
                    # Convert timestamp to a readable format
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = timestamp
                
                # Create keyboard buttons for each broadcast
                keyboard = [
                    [
                        InlineKeyboardButton("🗑️ Delete", callback_data=f"delbroadcast:{broadcast_id}"),
                        InlineKeyboardButton("📝 View Details", callback_data=f"viewbroadcast:{broadcast_id}")
                    ]
                ]
                
                # Send information for each broadcast with inline buttons
                update.message.reply_text(
                    f"*Broadcast Details*\n\n"
                    f"🆔 ID: `{broadcast_id}`\n"
                    f"⏰ Time: {formatted_time}\n"
                    f"📨 Sent to: {sent_count} chats\n"
                    f"📝 Message: {message_preview}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
            
            return
        else:
            update.message.reply_text(
                "Please provide a broadcast ID to delete.\n\n"
                "Usage: `/delbroadcast BROADCAST_ID`\n\n"
                "No recent broadcasts found.",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    broadcast_id = context.args[0]
    
    if 'broadcasts' not in context.bot_data or broadcast_id not in context.bot_data['broadcasts']:
        update.message.reply_text(f"❌ Broadcast with ID {broadcast_id} not found.")
        return
    
    broadcast = context.bot_data['broadcasts'][broadcast_id]
    sent_messages = broadcast.get('sent_messages', [])
    message_preview = broadcast['message'][:100] + "..." if len(broadcast['message']) > 100 else broadcast['message']
    
    # Ask for confirmation before deletion with Yes/No buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete all", callback_data=f"confirm_delbroadcast:{broadcast_id}"),
            InlineKeyboardButton("❌ No, cancel", callback_data="cancel_delbroadcast")
        ]
    ]
    
    update.message.reply_text(
        f"🗑️ *Delete Broadcast Confirmation*\n\n"
        f"You are about to delete this broadcast from {len(sent_messages)} chats:\n\n"
        f"Message: {message_preview}\n\n"
        f"Are you sure you want to proceed?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
