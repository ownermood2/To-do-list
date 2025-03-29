import os
import logging
import sys
import time
import traceback
import subprocess
from datetime import datetime

# Ensure we have the right python-telegram-bot version
try:
    from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
    from telegram import BotCommand
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
        from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
        from telegram import BotCommand
        from telegram.error import (TelegramError, Unauthorized, BadRequest,
                                  TimedOut, ChatMigrated, NetworkError)
        logging.info("Successfully installed and imported python-telegram-bot v13.7")
    except Exception as e:
        logging.error(f"Failed to install python-telegram-bot: {e}")
        raise

# Set up enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("main.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import our modules
from config import TELEGRAM_TOKEN
from bot import create_bot
from web_server import app

# Track restart attempts
MAX_RESTART_ATTEMPTS = 5
restart_count = 0
last_restart_time = None
uptime_start = datetime.now()

def log_uptime():
    """Log the current uptime of the bot"""
    current_time = datetime.now()
    uptime = current_time - uptime_start
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info(f"Bot uptime: {int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")
    return uptime

def handle_error(error):
    """Handle errors that occur during bot operation"""
    global restart_count, last_restart_time
    
    logger.error(f"Bot encountered an error: {error}")
    logger.error(traceback.format_exc())
    
    # Check if we should attempt a restart
    current_time = time.time()
    
    # Reset restart count if last restart was more than 1 hour ago
    if last_restart_time and (current_time - last_restart_time > 3600):
        restart_count = 0
    
    # Only restart if we haven't exceeded the maximum number of restart attempts
    if restart_count < MAX_RESTART_ATTEMPTS:
        restart_count += 1
        last_restart_time = current_time
        logger.info(f"Attempting to restart bot (attempt {restart_count}/{MAX_RESTART_ATTEMPTS})")
        return True
    else:
        logger.error(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Not restarting.")
        return False

# Main function
def main():
    """Start the bot with error handling and auto-restart."""
    global restart_count
    
    # Check if the script is run directly (as the Telegram bot)
    if __name__ == "__main__" and not os.environ.get("WEB_SERVER_ONLY", False):
        retry = True
        
        while retry:
            try:
                # Create and run the bot
                updater = create_bot()
                # Start the Bot
                logger.info("Starting Telegram bot")
                updater.start_polling(drop_pending_updates=True)
                
                # Schedule periodic uptime logging
                def log_uptime_job(context):
                    log_uptime()
                
                updater.job_queue.run_repeating(log_uptime_job, interval=3600, first=3600)  # Log uptime every hour
                
                # Schedule automatic cleanup of old messages in group chats (once per day)
                def auto_cleanup_job(context):
                    logger.info("Running scheduled auto-cleanup task")
                    try:
                        from auto_cleanup import clean_old_messages
                        clean_old_messages(TELEGRAM_TOKEN, days_old=7)
                        logger.info("Scheduled auto-cleanup completed successfully")
                    except Exception as e:
                        logger.error(f"Scheduled auto-cleanup failed: {e}")
                
                # Run once a day at 3:00 AM UTC
                from datetime import time as datetime_time
                cleanup_time = datetime_time(hour=3, minute=0)
                updater.job_queue.run_daily(auto_cleanup_job, time=cleanup_time)
                
                # Reset restart counter after successful start
                restart_count = 0
                
                # Run the bot until you press Ctrl-C or an error occurs
                updater.idle()
                
                # If we get here normally (through a clean shutdown), don't retry
                retry = False
                
            except Exception as e:
                # Log the error
                retry = handle_error(e)
                
                if retry:
                    # Wait before restarting
                    wait_time = min(30 * restart_count, 300)  # Exponential backoff, max 5 minutes
                    logger.info(f"Waiting {wait_time} seconds before restart...")
                    time.sleep(wait_time)
    else:
        # Import for Flask/gunicorn
        logger.info("Not starting bot, only importing app for gunicorn")
        retry = False

# Telegram bot initialization
if __name__ == "__main__":
    # Run the bot
    main()
else:
    # Flask/gunicorn import
    # We still need to initialize some things
    main()

# Make the app available for gunicorn
if not os.environ.get("TELEGRAM_BOT_ONLY", False):
    from web_server import app
else:
    app = None