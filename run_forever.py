#!/usr/bin/env python3
"""
Telegram Bot 24/7 Runner Script
This script ensures the Telegram bot stays running continuously, restarting it
if it crashes or is terminated for any reason.
"""

import os
import sys
import time
import logging
import subprocess
import signal
import datetime
import traceback

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("forever.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("forever")

# Configuration
CHECK_INTERVAL = 10  # Seconds between status checks
MAX_RESTART_COUNT = 10  # Maximum number of restarts in a short period
RESTART_WINDOW = 3600  # Window for counting restarts (1 hour)
MAX_BACKOFF = 300  # Maximum backoff time between restarts (5 minutes)

# Global variables
start_time = datetime.datetime.now()
restarts = []  # List of restart timestamps
current_process = None

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down...")
    if current_process:
        try:
            logger.info("Terminating bot process...")
            current_process.terminate()
            time.sleep(2)  # Give it a moment to terminate gracefully
            
            # If still running, kill it
            if current_process.poll() is None:
                logger.info("Bot process still running, killing...")
                current_process.kill()
        except Exception as e:
            logger.error(f"Error terminating bot process: {e}")
    
    logger.info("Runner exiting...")
    sys.exit(0)

def log_uptime():
    """Log the total uptime of the runner"""
    uptime = datetime.datetime.now() - start_time
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info(f"Runner uptime: {int(days)} days, {int(hours)} hours, {int(minutes)} minutes")

def calculate_backoff():
    """Calculate exponential backoff time based on recent restarts"""
    # Clean up old restarts
    global restarts
    now = time.time()
    restarts = [t for t in restarts if now - t < RESTART_WINDOW]
    
    # Calculate backoff (exponential with jitter)
    if not restarts:
        return 1  # First restart, no delay
    
    # Calculate backoff based on number of recent restarts
    count = len(restarts)
    backoff = min(2 ** count, MAX_BACKOFF)
    
    return backoff

def start_bot():
    """Start the Telegram bot as a subprocess"""
    global current_process
    
    try:
        logger.info("Starting Telegram bot...")
        
        # Use subprocess to start the bot
        current_process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        logger.info(f"Started bot process with PID: {current_process.pid}")
        
        # Non-blocking read from process output
        return current_process
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        logger.error(traceback.format_exc())
        return None

def monitor_bot(process):
    """Monitor the bot process and its output"""
    try:
        # Check if process has output to read
        if process.stdout:
            line = process.stdout.readline()
            if line:
                # Log the bot's output with a prefix
                line = line.strip()
                if line:
                    logger.info(f"[BOT] {line}")
                return True
        
        # Check if process is still running
        if process.poll() is not None:
            # Process has terminated
            exit_code = process.returncode
            logger.warning(f"Bot process has terminated with exit code: {exit_code}")
            
            # Collect any remaining output
            remaining_output = process.stdout.read()
            if remaining_output:
                for line in remaining_output.splitlines():
                    logger.info(f"[BOT] {line}")
            
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error monitoring bot: {e}")
        return False

def main():
    """Main runner function that keeps the bot alive"""
    global current_process, restarts
    
    logger.info("=== TaskMaster Pro Telegram Bot 24/7 Runner ===")
    logger.info(f"Started at: {start_time.isoformat()}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while True:
        # Start bot if not running
        if current_process is None or current_process.poll() is not None:
            # If this is a restart, record it and calculate backoff
            if current_process is not None:
                restarts.append(time.time())
                
                # Check if we've restarted too many times
                if len(restarts) > MAX_RESTART_COUNT:
                    backoff = calculate_backoff()
                    logger.warning(f"Too many restarts ({len(restarts)}/{MAX_RESTART_COUNT}), backing off for {backoff} seconds...")
                    time.sleep(backoff)
            
            # Start the bot
            current_process = start_bot()
            
            # If we couldn't start it, wait and try again
            if not current_process:
                logger.error("Failed to start bot process, waiting 30 seconds to retry...")
                time.sleep(30)
                continue
        
        # Monitor the bot
        if not monitor_bot(current_process):
            logger.warning("Bot process needs restart")
            time.sleep(5)  # Brief delay before restart
            current_process = None
            continue
        
        # Periodic uptime logging
        if int(time.time()) % 3600 < CHECK_INTERVAL:  # Approximately every hour
            log_uptime()
        
        # Short sleep between checks
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Runner stopped by user")
    except Exception as e:
        logger.critical(f"Runner crashed: {e}")
        logger.critical(traceback.format_exc())