import logging
import time
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)
from telegram import BotCommand, Update
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
    button_callback_handler,
    text_message_handler,
    error_handler,
    broadcast_handler,
    stats_handler,
    maintenance_handler,
    debug_handler
)
from database import initialize_database, save_data

logger = logging.getLogger(__name__)

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
    # Prepare command list for regular users
    commands = [BotCommand(command, description) for command, description in COMMANDS.items()]
    
    # Set commands
    updater.bot.set_my_commands(commands)
    logger.info("Bot commands have been set up")

def create_bot():
    """Create and configure the bot application"""
    # Check if token is available
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")
    
    # Initialize the bot and database
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    initialize_database()
    
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
    
    # Developer command handlers
    dispatcher.add_handler(CommandHandler("broadcast", broadcast_handler))
    dispatcher.add_handler(CommandHandler("stats", stats_handler))
    dispatcher.add_handler(CommandHandler("maintenance", maintenance_handler))
    dispatcher.add_handler(CommandHandler("debug", debug_handler))
    
    # Add callback query handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Add general message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_message_handler))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Schedule the reminder check job
    job_queue = updater.job_queue
    job_queue.run_repeating(check_reminders, interval=REMINDER_CHECK_INTERVAL, first=10)
    
    # Setup commands in the bot menu
    setup_commands(updater)
    
    logger.info("Bot has been fully configured")
    return updater
