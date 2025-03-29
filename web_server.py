import logging
import os
import sys
import time
import json
import datetime
import subprocess
import psutil
from flask import Flask, render_template, jsonify, request

# Import configurations
from config import BOT_NAME, VERSION, REPOSITORY_URL

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("webserver.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Function to check if the bot process is running
def is_bot_process_running():
    """Check if the bot process is running"""
    try:
        # Look for Python processes running main.py or run_forever.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and len(cmdline) > 1:
                    if ('python' in cmdline[0].lower() and 
                        ('main.py' in cmdline[1] or 'run_forever.py' in cmdline[1])):
                        return True, proc.info.get('pid')
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False, None
    except Exception as e:
        logger.error(f"Error checking bot process: {e}")
        return False, None

# Function to get uptime and logs
def get_bot_status():
    """Get detailed status about the bot"""
    status = {"running": False}
    
    # Check if process is running
    is_running, pid = is_bot_process_running()
    status["running"] = is_running
    
    if is_running:
        status["pid"] = pid
        
        # Try to get stats from database
        try:
            from database import get_stats
            status["stats"] = get_stats()
        except Exception as e:
            status["stats_error"] = str(e)
    
    # Check log files for additional information
    try:
        log_files = ["forever.log", "main.log"]
        log_info = {}
        
        for log_file in log_files:
            if os.path.exists(log_file):
                # Get file size and modification time
                file_stats = os.stat(log_file)
                log_info[log_file] = {
                    "size": file_stats.st_size,
                    "last_modified": datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                }
                
                # Get last few lines from log
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        log_info[log_file]["last_lines"] = lines[-10:] if lines else []
                except Exception as e:
                    log_info[log_file]["read_error"] = str(e)
        
        status["logs"] = log_info
    except Exception as e:
        status["log_error"] = str(e)
    
    return status

# Flask app for web interface
app = Flask(__name__)

@app.route('/')
def index():
    """Main page - status and info about the bot"""
    # Get running status
    is_running, _ = is_bot_process_running()
    
    return jsonify({
        "status": "running" if is_running else "stopped",
        "bot_name": BOT_NAME,
        "version": VERSION,
        "repository": REPOSITORY_URL,
        "description": "Professional task management bot for individuals and groups",
        "server_time": datetime.datetime.now().isoformat(),
        "features": [
            "Task creation with priorities, categories, and deadlines",
            "Smart reminders and notifications",
            "Advanced filtering and search capabilities",
            "Productivity statistics and insights",
            "Seamless group integration and collaboration",
            "Automatic group joining via invitation links",
            "24/7 operation with automatic recovery"
        ]
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    # Enhanced health check that verifies bot is running
    is_running, _ = is_bot_process_running()
    
    if is_running:
        return jsonify({"status": "ok", "bot_running": True})
    else:
        # Still return 200 but indicate bot is not running
        return jsonify({"status": "degraded", "bot_running": False, 
                        "message": "Bot process is not running"})

@app.route('/bot/status')
def bot_status():
    """Check the status of the Telegram bot"""
    # Get detailed status information
    status = get_bot_status()
    return jsonify(status)

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Start the Telegram bot"""
    try:
        # Check if already running
        is_running, pid = is_bot_process_running()
        if is_running:
            return jsonify({
                "status": "success", 
                "message": f"Bot already running with PID {pid}"
            })
        
        # Use the run_forever.py for better resilience
        logger.info("Starting bot using run_forever.py")
        subprocess.Popen([sys.executable, 'run_forever.py'], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True)
        
        # Brief delay to allow process to start
        time.sleep(1)
        
        # Verify it started
        is_running, pid = is_bot_process_running()
        if is_running:
            return jsonify({
                "status": "success", 
                "message": f"Bot started successfully with PID {pid}"
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot start initiated but process not detected"
            })
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    """Stop the Telegram bot"""
    try:
        # Check if running
        is_running, pid = is_bot_process_running()
        if not is_running:
            return jsonify({
                "status": "success", 
                "message": "Bot is not running"
            })
        
        # Try to terminate the process
        if pid:
            try:
                process = psutil.Process(pid)
                process.terminate()
                # Wait briefly for termination
                gone, still_alive = psutil.wait_procs([process], timeout=3)
                if still_alive:
                    # Force kill if still running
                    process.kill()
                return jsonify({
                    "status": "success", 
                    "message": f"Bot with PID {pid} terminated"
                })
            except psutil.NoSuchProcess:
                return jsonify({
                    "status": "success", 
                    "message": f"Process with PID {pid} already terminated"
                })
            except Exception as e:
                logger.error(f"Error stopping process {pid}: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot appears to be running but PID not found"
            })
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/install')
def install_info():
    """Information about installing the bot"""
    bot_username = os.environ.get('BOT_USERNAME', 'TaskMasterProBot')
    
    # Get available commands for display
    from config import COMMANDS
    command_list = [f"/{cmd} - {desc}" for cmd, desc in COMMANDS.items()]
    
    return jsonify({
        "bot_name": BOT_NAME,
        "version": VERSION,
        "repository": REPOSITORY_URL,
        "bot_username": bot_username,
        "installation_link": f"https://t.me/{bot_username}",
        "instructions": "Click the link above to start a conversation with the bot, or search for it in Telegram.",
        "features": [
            "Personal and group task management",
            "Task priorities (High, Medium, Low)",
            "Custom categories and tags",
            "Due date filtering and reminders",
            "Productivity statistics and completion tracking",
            "Intuitive command interface with inline buttons",
            "24/7 operation with automatic recovery",
            "Smart reminders and notifications",
            "Team collaboration tools"
        ],
        "commands": command_list,
        "group_features": [
            "Shared task lists visible to all members",
            "Team productivity tracking",
            "Automatic joining via invitation links",
            "Task assignment using @mentions",
            "Automatic conversation cleanup",
            "Group statistics and insights"
        ],
        "running_status": is_bot_process_running()[0]
    })

# Define the app variable for gunicorn
app = app

if __name__ == "__main__":
    # Run the Flask web app
    logger.info("Starting Flask web app")
    app.run(host="0.0.0.0", port=5000, debug=True)