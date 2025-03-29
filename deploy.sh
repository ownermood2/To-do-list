#!/bin/bash

# TaskMaster Pro Telegram Bot Deployment Script
# This script sets up and runs the bot in a persistent manner

# Ensure the script exits if any command fails
set -e

echo "=== TaskMaster Pro Telegram Bot Deployment ==="
echo "Starting deployment process at $(date)"

# Make sure environment variables are set
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "Error: TELEGRAM_TOKEN environment variable is not set"
    echo "Please set it before running this script"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p logs

# Install required system packages if needed
echo "Checking system dependencies..."
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux for persistent sessions..."
    apt-get update && apt-get install -y tmux
fi

# Function to start the bot in a tmux session
start_bot() {
    echo "Starting bot in a persistent tmux session..."
    
    # Kill existing session if it exists
    tmux kill-session -t taskmaster 2>/dev/null || true
    
    # Create a new detached session
    tmux new-session -d -s taskmaster
    
    # Send commands to the session
    tmux send-keys -t taskmaster "cd $(pwd)" C-m
    tmux send-keys -t taskmaster "python run_forever.py > logs/stdout.log 2> logs/stderr.log" C-m
    
    echo "Bot started in tmux session 'taskmaster'"
    echo "To attach to the session: tmux attach -t taskmaster"
    echo "To detach from the session once attached: Ctrl+B followed by D"
}

# Function to check if the bot is running
check_bot() {
    if tmux has-session -t taskmaster 2>/dev/null; then
        echo "Bot is running in tmux session 'taskmaster'"
        
        # Show recent logs
        echo "Recent logs:"
        tail -n 10 logs/stdout.log || true
        
        return 0
    else
        echo "Bot is not running"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    echo "Stopping bot..."
    if tmux has-session -t taskmaster 2>/dev/null; then
        tmux kill-session -t taskmaster
        echo "Bot stopped"
    else
        echo "Bot was not running"
    fi
}

# Command handling
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        stop_bot
        sleep 2
        start_bot
        ;;
    status)
        check_bot
        ;;
    logs)
        echo "Showing logs (Ctrl+C to exit):"
        tail -f logs/stdout.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "  start    - Start the bot in a persistent tmux session"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  status   - Check if the bot is running"
        echo "  logs     - Show live logs"
        ;;
esac

echo "Deployment script completed at $(date)"