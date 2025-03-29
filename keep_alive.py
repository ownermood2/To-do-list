import os
import time
import logging
import subprocess
import signal
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_watchdog.log'
)
logger = logging.getLogger('keep_alive')

def get_bot_process():
    """Check if bot process is running and return it"""
    try:
        # Run ps command to find python processes running main.py
        result = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.splitlines():
            if "python" in line and "main.py" in line and "grep" not in line:
                # Extract PID
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1])
    except Exception as e:
        logger.error(f"Error checking bot process: {e}")
    
    return None

def start_bot():
    """Start the Telegram bot process"""
    try:
        logger.info("Starting Telegram bot...")
        # Using nohup to make the process independent from the terminal
        process = subprocess.Popen(
            ["nohup", "python", "main.py", "&"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        logger.info(f"Bot started with PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return None

def main():
    """Main watchdog function to keep the bot running"""
    logger.info("Starting bot watchdog service")
    
    # Keep watchdog running forever
    while True:
        pid = get_bot_process()
        
        if pid:
            logger.info(f"Bot is running with PID: {pid}")
        else:
            logger.warning("Bot is not running! Starting it...")
            start_bot()
        
        # Log timestamp for monitoring
        logger.info(f"Watchdog check: {datetime.now().isoformat()}")
        
        # Wait before next check
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Watchdog service stopped by user")
    except Exception as e:
        logger.error(f"Watchdog service crashed: {e}")