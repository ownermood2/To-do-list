#!/usr/bin/env python3
"""
Auto Cleanup Script for TaskMaster Pro Bot
This script automates the cleanup of old messages in group chats to maintain 
cleanliness and avoid cluttering the chat history.
"""

import os
import logging
import time
from datetime import datetime, timedelta

try:
    from telegram import Bot
    from telegram.error import TelegramError, BadRequest, Unauthorized
except ImportError:
    import subprocess
    import sys
    logging.warning("Required telegram modules not found or incorrect version.")
    logging.info("Installing python-telegram-bot v13.7...")
    try:
        # Uninstall any existing version
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "python-telegram-bot"])
        # Install the specific version
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"])
        # Now import again
        from telegram import Bot
        from telegram.error import TelegramError, BadRequest, Unauthorized
        logging.info("Successfully installed and imported python-telegram-bot v13.7")
    except Exception as e:
        logging.error(f"Failed to install python-telegram-bot: {e}")
        raise

from database import get_data, get_all_chat_ids
from config import TELEGRAM_TOKEN, CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("auto_cleanup.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def clean_old_messages(bot_token, days_old=7):
    """
    Clean up old bot messages from group chats
    
    Args:
        bot_token (str): The Telegram bot token
        days_old (int): Messages older than this many days will be cleaned up
    """
    bot = Bot(token=bot_token)
    data = get_data()
    chat_ids = get_all_chat_ids()
    
    logger.info(f"Starting automatic cleanup of messages older than {days_old} days")
    
    # Only clean group chats
    group_count = 0
    message_count = 0
    failed_count = 0
    
    # Calculate cutoff date
    cutoff_time = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_time.timestamp()
    
    for chat_id_str in chat_ids:
        try:
            chat_id = int(chat_id_str)
            chat_data = data.get(chat_id_str, {})
            
            # Skip non-group chats
            chat_type = chat_data.get('type')
            if chat_type not in [CHAT_TYPE_GROUP, CHAT_TYPE_SUPERGROUP]:
                continue
                
            group_count += 1
            
            # Check if we have message records for this chat
            if 'bot_messages' in chat_data:
                # List of message IDs that were successfully cleaned
                cleaned_messages = []
                
                for msg_id, msg_data in chat_data['bot_messages'].items():
                    # Check if message is older than the cutoff date
                    msg_time = msg_data.get('timestamp', 0)
                    if msg_time < cutoff_timestamp:
                        try:
                            # Try to delete the message
                            bot.delete_message(chat_id=chat_id, message_id=int(msg_id))
                            cleaned_messages.append(msg_id)
                            message_count += 1
                            
                            # Add a small delay to avoid hitting rate limits
                            time.sleep(0.1)
                        except (BadRequest, TelegramError) as e:
                            # Message may already be deleted or too old
                            cleaned_messages.append(msg_id)
                            logger.debug(f"Couldn't delete message {msg_id} in chat {chat_id}: {e}")
                            failed_count += 1
                
                # Remove deleted messages from the record
                for msg_id in cleaned_messages:
                    chat_data['bot_messages'].pop(msg_id, None)
                
                # Log the cleanup
                if cleaned_messages:
                    logger.info(f"Cleaned up {len(cleaned_messages)} messages in chat {chat_id}")
        
        except Exception as e:
            logger.error(f"Error cleaning chat {chat_id_str}: {e}")
    
    logger.info(f"Auto-cleanup complete. Processed {group_count} groups, cleaned {message_count} messages, {failed_count} failed")

def main():
    """Run the cleanup process"""
    # Get token from environment variable
    token = TELEGRAM_TOKEN
    
    if not token:
        logger.error("No bot token found. Please set the TELEGRAM_TOKEN environment variable.")
        return
    
    try:
        # Clean messages older than 7 days
        clean_old_messages(token, days_old=7)
    except Exception as e:
        logger.error(f"Auto-cleanup failed: {e}")

if __name__ == "__main__":
    main()