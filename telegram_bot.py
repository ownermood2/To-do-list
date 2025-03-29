import logging
import os
from bot import create_bot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Create and start the bot
    logger.info("Starting Todo List Bot")
    bot = create_bot()
    bot.run_polling()