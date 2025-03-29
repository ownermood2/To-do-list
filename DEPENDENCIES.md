# TaskMaster Pro Dependencies

This document outlines the required dependencies for the TaskMaster Pro Telegram bot.

## Python Requirements

The bot is built with Python and requires Python 3.7 or higher. The following Python packages are required:

- **python-telegram-bot==13.7**
  - Core Telegram bot functionality
  - Specific version is required for compatibility
  
- **flask**
  - Web server for monitoring and control dashboard
  
- **gunicorn**
  - Production-ready WSGI server for Flask
  
- **psutil**
  - System monitoring and process management
  
## System Requirements (Optional)

For the deploy.sh script to work properly in production environment:

- **tmux**
  - Terminal multiplexer for persistent sessions
  - Used by the deployment script to run the bot in background

## Environment Variables

The following environment variables should be configured:

- **TELEGRAM_TOKEN**
  - Required: Your Telegram bot token from BotFather
  
- **DEVELOPER_IDS**
  - Optional: Comma-separated list of Telegram user IDs for developer access
  - Example: "123456789,987654321"

## Installation

The easiest way to install all dependencies is to run the provided setup script:

```bash
./setup_environment.sh
```

## Troubleshooting

If you encounter issues with the python-telegram-bot package, try the following:

1. Uninstall any existing installation:
   ```bash
   pip uninstall -y python-telegram-bot telegram
   ```

2. Install the specific version:
   ```bash
   pip install python-telegram-bot==13.7
   ```

## Docker Deployment (Future)

A Dockerfile will be provided in a future update for containerized deployment.