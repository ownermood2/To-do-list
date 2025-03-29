import logging
import os
import sys
from web_server import app

# This file exists to serve as the main entry point for gunicorn
# The actual Flask app is defined in web_server.py

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Run the Flask web app
    logger.info("Starting Flask web app")
    app.run(host="0.0.0.0", port=5000, debug=True)