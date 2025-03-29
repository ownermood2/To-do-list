import logging
import os
import sys
import subprocess
from flask import Flask, render_template, jsonify

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Flask app for web interface
app = Flask(__name__)

@app.route('/')
def index():
    """Main page - status and info about the bot"""
    return jsonify({
        "status": "running",
        "bot_name": "Telegram Todo List Bot",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/bot/status')
def bot_status():
    """Check the status of the Telegram bot"""
    # In a production environment, we would check if the bot is actually running
    try:
        from database import get_stats
        stats = get_stats()
        return jsonify({
            "status": "running",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Start the Telegram bot"""
    try:
        # Use subprocess to run the bot in the background
        subprocess.Popen([sys.executable, 'main.py'], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True)
        return jsonify({"status": "success", "message": "Bot started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/install')
def install_info():
    """Information about installing the bot"""
    bot_username = os.environ.get('BOT_USERNAME', 'YourTodoListBot')
    return jsonify({
        "bot_username": bot_username,
        "installation_link": f"https://t.me/{bot_username}",
        "instructions": "Click the link above to start a conversation with the bot, or search for it in Telegram."
    })

# Define the app variable for gunicorn
app = app

if __name__ == "__main__":
    # Run the Flask web app
    logger.info("Starting Flask web app")
    app.run(host="0.0.0.0", port=5000, debug=True)