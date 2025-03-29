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

def main():
    """Start the bot."""
    # Create and run the bot
    updater = create_bot()
    # Start the Bot
    logger.info("Starting Telegram bot")
    updater.start_polling()
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == "__main__":
    # Run the bot
    try:
        # Set the environment variable to indicate that we're only running the bot
        os.environ["TELEGRAM_BOT_ONLY"] = "True"
        main()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)