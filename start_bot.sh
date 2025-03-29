#!/bin/bash

# This script starts the TaskMaster Pro bot with the persistent runner
# A simpler alternative to deploy.sh for direct execution

# Create logs directory if it doesn't exist
mkdir -p logs

# Check for required environment variables
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "ERROR: TELEGRAM_TOKEN environment variable is not set!"
    echo "Please set it before running this script:"
    echo "export TELEGRAM_TOKEN=your_token_here"
    exit 1
fi

echo "==============================================="
echo "Starting TaskMaster Pro Telegram Bot..."
echo "Started at: $(date)"
echo "Platform: $(uname -a)"
echo "Log files will be created in the logs directory"
echo "Press Ctrl+C to stop the bot"
echo "==============================================="

# Run with output to both console and log file
python run_forever.py 2>&1 | tee logs/bot_$(date +%Y%m%d_%H%M%S).log