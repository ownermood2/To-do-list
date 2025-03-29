import os
import logging
import sys
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import BotCommand

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Import our modules
from config import TELEGRAM_TOKEN
from bot import create_bot
from web_server import app

# Main function
def main():
    """Start the bot."""
    # Check if the script is run directly (as the Telegram bot)
    if __name__ == "__main__" and not os.environ.get("WEB_SERVER_ONLY", False):
        # Create and run the bot
        updater = create_bot()
        # Start the Bot
        logger.info("Starting Telegram bot")
        updater.start_polling()
        # Run the bot until you press Ctrl-C
        updater.idle()
    else:
        # Import for Flask/gunicorn
        logger.info("Not starting bot, only importing app for gunicorn")

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