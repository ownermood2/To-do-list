#!/bin/bash

# TaskMaster Pro Environment Setup Script
# This script ensures all the required dependencies are installed correctly

echo "=== TaskMaster Pro Environment Setup ==="
echo "Setting up environment at $(date)"

# Make sure we have the right versions
echo "Resolving dependencies..."

# Uninstall potentially conflicting packages
echo "Removing any conflicting packages..."
pip uninstall -y telegram python-telegram-bot

# Install the specific version of python-telegram-bot and other dependencies
echo "Installing required packages..."
pip install python-telegram-bot==13.7 psutil flask gunicorn

# Create necessary directories
mkdir -p logs

# Check if required environment variables are set
echo "Checking environment variables..."
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "WARNING: TELEGRAM_TOKEN environment variable is not set"
    echo "You will need to set this before starting the bot"
else
    echo "TELEGRAM_TOKEN is set ✓"
fi

if [ -z "$DEVELOPER_IDS" ]; then
    echo "WARNING: DEVELOPER_IDS environment variable is not set"
    echo "Developer commands won't be available"
else
    echo "DEVELOPER_IDS is set ✓"
fi

# Make scripts executable
echo "Setting execute permissions on scripts..."
chmod +x run_forever.py deploy.sh start_bot.sh

echo "Environment setup complete! ✅"
echo "To start the bot, use one of the following methods:"
echo "1. ./run_forever.py             (directly run the persistent bot)"
echo "2. ./deploy.sh start            (start in a tmux session)"
echo "3. ./start_bot.sh               (simple start script)"
echo "4. Restart the Replit workflow  (automatic start)"