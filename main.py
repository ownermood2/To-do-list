import logging
import os
import sys
from flask import Flask, render_template, jsonify

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
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

# This helps separate the Flask app and Telegram bot functionality
if __name__ == "__main__":
    # Check if we should run the bot or the web app based on the workflow
    if len(sys.argv) > 1 and sys.argv[1] == "bot":
        # Run the Telegram bot
        from bot import create_bot
        logger.info("Starting Todo List Bot")
        bot = create_bot()
        bot.run_polling()
    else:
        # Run the Flask web app
        logger.info("Starting Flask web app")
        app.run(host="0.0.0.0", port=5000, debug=True)
