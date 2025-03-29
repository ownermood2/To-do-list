#!/bin/bash
# Start TaskMaster Pro bot in 24/7 continuous mode

echo "======================================="
echo "TaskMaster Pro Telegram Bot - 24/7 Mode"
echo "======================================="
echo "Starting bot with continuous operation mode..."

# Make sure log directory exists
mkdir -p logs

# Function to check if a process is running
is_running() {
    if ps -p $1 > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Export environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if TELEGRAM_TOKEN is set
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "ERROR: TELEGRAM_TOKEN environment variable is not set"
    echo "Please set the TELEGRAM_TOKEN environment variable and try again"
    exit 1
fi

# Kill any existing instances
echo "Checking for existing bot processes..."
pkill -f "python run_forever.py" || true
pkill -f "python main.py" || true

# Wait for processes to terminate
sleep 2

# Start the bot in background with logging
echo "Starting bot in 24/7 mode..."
nohup python run_forever.py > logs/forever.log 2>&1 &
RUNNER_PID=$!

# Check if process started successfully
if is_running $RUNNER_PID; then
    echo "Bot started successfully with runner PID: $RUNNER_PID"
    echo "View logs with: tail -f logs/forever.log"
    echo "To stop the bot, run: ./stop_bot.sh"
    
    # Save PID for later use
    echo $RUNNER_PID > .runner_pid
    exit 0
else
    echo "Failed to start bot. Check logs for details."
    exit 1
fi