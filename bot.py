import logging
import time
import os
import signal
import sys
import subprocess
from datetime import datetime

# Ensure we have the right python-telegram-bot version
try:
    from telegram.ext import (
        Updater,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        Filters,
        CallbackContext
    )
    from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.error import (TelegramError, Unauthorized, BadRequest,
                               TimedOut, ChatMigrated, NetworkError)
except ImportError:
    logging.warning("Required telegram modules not found or incorrect version.")
    logging.info("Installing python-telegram-bot v13.7...")
    try:
        # Uninstall any existing version
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "python-telegram-bot"])
        # Install the specific version
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"])
        # Now import again
        from telegram.ext import (
            Updater,
            CommandHandler,
            MessageHandler,
            CallbackQueryHandler,
            Filters,
            CallbackContext
        )
        from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import (TelegramError, Unauthorized, BadRequest,
                                   TimedOut, ChatMigrated, NetworkError)
        logging.info("Successfully installed and imported python-telegram-bot v13.7")
    except Exception as e:
        logging.error(f"Failed to install python-telegram-bot: {e}")
        raise
from config import TELEGRAM_TOKEN, COMMANDS, DEVELOPER_COMMANDS, REMINDER_CHECK_INTERVAL
from handlers import (
    start_handler,
    help_handler,
    add_task_handler,
    list_tasks_handler,
    done_task_handler,
    delete_task_handler, 
    clear_tasks_handler,
    remind_task_handler,
    settings_handler,
    join_group_handler,
    today_tasks_handler,
    week_tasks_handler,
    priority_task_handler,
    tag_task_handler,
    search_tasks_handler,
    user_stats_handler,
    clean_chat_handler,
    button_callback_handler,
    text_message_handler,
    error_handler,
    broadcast_handler,
    groupcast_handler,
    delete_broadcast_handler,
    adddev_handler,
    stats_handler,
    maintenance_handler,
    debug_handler
)
from database import initialize_database, save_data

# Set up more detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Track bot uptime
BOT_START_TIME = datetime.now()

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received shutdown signal, saving data and exiting gracefully...")
    # Perform any necessary cleanup
    try:
        save_data()
        logger.info("Data saved successfully")
    except Exception as e:
        logger.error(f"Error saving data during shutdown: {e}")
    
    logger.info(f"Bot shutting down, uptime: {datetime.now() - BOT_START_TIME}")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_reminders(context: CallbackContext):
    """Check for due reminders and send notifications"""
    from database import get_data
    data = get_data()
    current_time = time.time()
    
    reminders_to_send = []
    
    # Scan all users and groups for due reminders
    for chat_id, chat_data in data.items():
        if 'tasks' not in chat_data:
            continue
            
        for task_id, task in enumerate(chat_data['tasks']):
            if not task.get('active', True):
                continue
                
            reminder = task.get('reminder')
            if reminder and reminder <= current_time and not task.get('reminded', False):
                reminders_to_send.append((chat_id, task_id, task))
                # Mark as reminded to avoid duplicate reminders
                task['reminded'] = True
    
    # Send reminders
    for chat_id, task_id, task in reminders_to_send:
        try:
            context.bot.send_message(
                chat_id=int(chat_id),
                text=f"⏰ *Reminder*: {task['text']}",
                parse_mode="Markdown"
            )
            logger.debug(f"Sent reminder for task {task_id} to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    # Save changes to data
    if reminders_to_send:
        save_data(data)

def setup_commands(updater):
    """Set up the bot commands that appear in the menu"""
    try:
        # Import commands from the commands module
        from commands import USER_COMMANDS
        # Prepare command list for regular users
        commands = [BotCommand(cmd, info['description']) for cmd, info in USER_COMMANDS.items()]
    except (ImportError, KeyError):
        # Fallback to config if commands module is not working
        commands = [BotCommand(command, description) for command, description in COMMANDS.items()]
    
    # Set commands
    try:
        updater.bot.set_my_commands(commands)
        logger.info(f"Bot commands have been set up ({len(commands)} commands)")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")
        logger.info("Attempting to set commands without using BotCommand objects")
        try:
            # Attempt alternative method
            command_dict = {cmd.command: cmd.description for cmd in commands}
            updater.bot.set_my_commands([(cmd, desc) for cmd, desc in command_dict.items()])
            logger.info("Successfully set commands using alternative method")
        except Exception as e2:
            logger.error(f"Alternative method also failed: {e2}")

def create_bot():
    """Create and configure the bot application"""
    # Check if token is available
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")
    
    # Initialize the bot and database
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    initialize_database()
    
    try:
        # Try to use the improved command registration from commands.py
        from commands import register_commands
        
        # Create a handlers dictionary mapping command names to handler functions
        handlers = {
            # Basic commands
            'start': start_handler,
            'help': help_handler,
            'add': add_task_handler,
            'list': list_tasks_handler,
            'done': done_task_handler,
            'delete': delete_task_handler,
            'clear': clear_tasks_handler,
            'remind': remind_task_handler,
            'settings': settings_handler,
            'join': join_group_handler,
            
            # Enhanced commands
            'today': today_tasks_handler,
            'week': week_tasks_handler,
            'priority': priority_task_handler,
            'tag': tag_task_handler,
            'search': search_tasks_handler,
            'clean': clean_chat_handler,
            'stats': user_stats_handler,
            
            # Developer commands
            'broadcast': broadcast_handler,
            'groupcast': groupcast_handler,
            'delbroadcast': delete_broadcast_handler,
            'adddev': adddev_handler,
            'devstats': stats_handler,
            'maintenance': maintenance_handler,
            'debug': debug_handler,
        }
        
        # Register all commands using the improved handler
        register_commands(dispatcher, handlers)
        logger.info("Registered commands using commands.py module")
    except (ImportError, Exception) as e:
        logger.warning(f"Failed to use commands.py for registration: {e}. Falling back to manual registration.")
        # Manual fallback registration if commands.py import fails
        # Set up command handlers
        dispatcher.add_handler(CommandHandler("start", start_handler))
        dispatcher.add_handler(CommandHandler("help", help_handler))
        dispatcher.add_handler(CommandHandler("add", add_task_handler))
        dispatcher.add_handler(CommandHandler("list", list_tasks_handler))
        dispatcher.add_handler(CommandHandler("done", done_task_handler))
        dispatcher.add_handler(CommandHandler("delete", delete_task_handler))
        dispatcher.add_handler(CommandHandler("clear", clear_tasks_handler))
        dispatcher.add_handler(CommandHandler("remind", remind_task_handler))
        dispatcher.add_handler(CommandHandler("settings", settings_handler))
        dispatcher.add_handler(CommandHandler("join", join_group_handler))
        
        # New enhanced commands
        dispatcher.add_handler(CommandHandler("today", today_tasks_handler))
        dispatcher.add_handler(CommandHandler("week", week_tasks_handler))
        dispatcher.add_handler(CommandHandler("priority", priority_task_handler))
        dispatcher.add_handler(CommandHandler("tag", tag_task_handler))
        dispatcher.add_handler(CommandHandler("search", search_tasks_handler))
        dispatcher.add_handler(CommandHandler("clean", clean_chat_handler))
        
        # Developer command handlers
        dispatcher.add_handler(CommandHandler("broadcast", broadcast_handler))
        dispatcher.add_handler(CommandHandler("groupcast", groupcast_handler))
        dispatcher.add_handler(CommandHandler("delbroadcast", delete_broadcast_handler))
        dispatcher.add_handler(CommandHandler("adddev", adddev_handler))
        dispatcher.add_handler(CommandHandler("devstats", stats_handler))
        dispatcher.add_handler(CommandHandler("maintenance", maintenance_handler))
        dispatcher.add_handler(CommandHandler("debug", debug_handler))
        
        # Regular user stats command (different from developer stats)
        dispatcher.add_handler(CommandHandler("stats", user_stats_handler))
    
    # Add callback query handler for inline buttons (always needed)
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Add a handler for new group members (including the bot itself)
    def new_chat_members_handler(update: Update, context: CallbackContext) -> None:
        """Handle new chat members (including when bot is added to a group)"""
        # Check if the bot itself was added to the group
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    # Bot was added to the group, send an introduction
                    chat_id = update.effective_chat.id
                    chat_title = update.effective_chat.title
                    
                    # Update chat type in database
                    from database import update_chat_type
                    update_chat_type(chat_id, update.effective_chat.type)
                    
                    # Log the event
                    logger.info(f"Bot was added to group: {chat_title} (ID: {chat_id})")
                    
                    # Send welcome message with information about the bot
                    keyboard = [
                        [
                            InlineKeyboardButton("📚 View Commands", callback_data="group_help"),
                            InlineKeyboardButton("➕ Add Task", callback_data="show_add_format")
                        ]
                    ]
                    
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"👋 *Hello everyone in {chat_title}!*\n\n"
                            f"I'm *TaskMaster Pro*, your group's task management assistant. "
                            f"I can help you:\n\n"
                            f"• Create and manage tasks for the group\n"
                            f"• Send reminders about upcoming deadlines\n"
                            f"• Keep track of who's done what\n"
                            f"• Organize tasks by priority and category\n\n"
                            f"To get started, use the `/add` command to create your first task, "
                            f"or tap the buttons below to learn more!"
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    
                    # Wait a moment before sending a second message with quick tips
                    import time
                    time.sleep(1)
                    
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            "🔍 *Quick Tips:*\n\n"
                            "• `/add Buy snacks for meeting` - Creates a new task\n"
                            "• `/list` - Shows all active tasks\n"
                            "• `/help` - Shows all available commands\n"
                            "• `/clean` - Removes bot messages to keep chat tidy\n\n"
                            "I'll only respond to commands, not regular messages, "
                            "so I won't clutter your group chat!"
                        ),
                        parse_mode="Markdown"
                    )
    
    # Add handler for new members
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_members_handler))
    
    # Add general message handler (always needed)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message_handler))
    
    # Add error handler (always needed)
    dispatcher.add_error_handler(error_handler)
    
    # Schedule the reminder check job
    job_queue = updater.job_queue
    job_queue.run_repeating(check_reminders, interval=REMINDER_CHECK_INTERVAL, first=10)
    
    # Setup commands in the bot menu
    setup_commands(updater)
    
    logger.info("Bot has been fully configured")
    return updater
