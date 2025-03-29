#!/bin/bash
# Stop TaskMaster Pro bot

echo "======================================="
echo "TaskMaster Pro Telegram Bot - Stopping"
echo "======================================="

# Function to check if a process is running
is_running() {
    if ps -p $1 > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Check for runner PID file
if [ -f .runner_pid ]; then
    RUNNER_PID=$(cat .runner_pid)
    echo "Found runner process with PID: $RUNNER_PID"
    
    # Check if the process is actually running
    if is_running $RUNNER_PID; then
        echo "Stopping runner process..."
        kill $RUNNER_PID
        
        # Give it a moment to terminate gracefully
        echo "Waiting for process to terminate..."
        for i in {1..10}; do
            if ! is_running $RUNNER_PID; then
                break
            fi
            sleep 1
        done
        
        # If still running, force kill
        if is_running $RUNNER_PID; then
            echo "Process still running, forcing termination..."
            kill -9 $RUNNER_PID
        fi
        
        echo "Runner process terminated."
    else
        echo "Runner process not running."
    fi
    
    rm .runner_pid
fi

# Check for any remaining bot processes
echo "Checking for any remaining bot processes..."
BOT_PIDS=$(pgrep -f "python main.py" || true)
FOREVER_PIDS=$(pgrep -f "python run_forever.py" || true)

if [ ! -z "$BOT_PIDS" ]; then
    echo "Found running bot processes: $BOT_PIDS"
    echo "Terminating all bot processes..."
    pkill -f "python main.py" || true
    sleep 2
    pkill -9 -f "python main.py" || true
fi

if [ ! -z "$FOREVER_PIDS" ]; then
    echo "Found running runner processes: $FOREVER_PIDS"
    echo "Terminating all runner processes..."
    pkill -f "python run_forever.py" || true
    sleep 2
    pkill -9 -f "python run_forever.py" || true
fi

echo "Bot stopped successfully."
exit 0