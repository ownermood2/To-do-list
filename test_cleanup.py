#!/usr/bin/env python3
"""
Test Script for Auto Cleanup in TaskMaster Pro Bot
This script allows for testing the auto cleanup functionality without waiting for the scheduled job.
"""

import os
import logging
import argparse
from auto_cleanup import clean_old_messages
from config import TELEGRAM_TOKEN

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("test_cleanup.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run a test cleanup with optional days parameter"""
    parser = argparse.ArgumentParser(description='Test the auto-cleanup functionality.')
    parser.add_argument('--days', type=int, default=7, 
                        help='Default number of days for chats without settings (default: 7)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Get token from environment variable or config
    token = TELEGRAM_TOKEN
    
    if not token:
        logger.error("No bot token found. Please ensure the TELEGRAM_TOKEN environment variable is set.")
        return
    
    try:
        logger.info(f"Running test cleanup with default days={args.days}")
        clean_old_messages(token, default_days_old=args.days)
        logger.info("Test cleanup completed successfully")
    except Exception as e:
        logger.error(f"Test cleanup failed: {e}")

if __name__ == "__main__":
    main()