# TaskMaster Pro - Telegram Task Management Bot

A powerful Telegram bot designed for comprehensive task management, supporting both individual and collaborative productivity workflows. Built for professional use with 24/7 uptime and exceptional reliability.

## Features

- **Task Management**: Create, list, complete, and delete tasks
- **Advanced Filtering**: View tasks by priority, category, due date (/today, /week)
- **Smart Reminders**: Set automated reminders with flexible time formats
- **Group Support**: Collaborative task management in group chats
- **Interactive Interface**: User-friendly command system with inline buttons
- **Categories & Tags**: Organize tasks with custom categories and tags
- **Priority Levels**: Set task importance with priority flags
- **Chat Cleaning**: Keep conversations tidy with the /clean command and automatic cleanup feature
- **Automatic Group Joining**: Bot can join groups when provided with invitation links
- **24/7 Operation**: Persistent running with automatic recovery from crashes
- **Web Dashboard**: Monitor bot status and statistics via web interface

## Enhanced Time Format Support

TaskMaster Pro now supports a wide variety of time and date formats for setting reminders! You can use:

- Relative times: `1h 30m`, `2 hours 15 minutes`, `1:30`
- Days with times: `today 3pm`, `tomorrow 9am`, `friday 15:00`
- Specific dates: `4/20`, `apr 15`, `12-25 9am`
- Time of day: `3pm`, `15:00`, `9h30`

For a complete guide to all supported formats, see [TIME_FORMAT_GUIDE.md](TIME_FORMAT_GUIDE.md).

## Auto-Cleanup Feature

TaskMaster Pro includes an intelligent auto-cleanup system that automatically removes old bot messages from group chats to keep conversations tidy. This feature:

- Runs automatically once per day (at 3:00 AM UTC)
- Can be customized per chat through the `/settings` menu
- Allows setting different retention periods (3, 7, 14, or 30 days)
- Can be disabled completely for specific chats
- Respects chat-specific preferences

To manually test the auto-cleanup functionality, use the included script:
```
./run_cleanup.sh
```

You can also specify a custom default retention period:
```
./run_cleanup.sh --days 14
```

## Commands

- `/start` - Start the bot and get introductory information
- `/help` - Show all available commands and how to use them
- `/add` - Add a new task
- `/list` - Show all active tasks
- `/done` - Mark a task as completed
- `/delete` - Delete a task permanently
- `/clear` - Clear all tasks
- `/remind` - Set a reminder for a task
- `/today` - Show tasks due today
- `/week` - Show tasks due this week
- `/tag` - Add a category/tag to a task
- `/priority` - Set task priority
- `/search` - Search for tasks by keyword
- `/settings` - Configure bot settings
- `/clean` - Clean up bot messages from chat

## Setup

1. Clone this repository
2. Run the setup script to install all dependencies: `./setup_environment.sh`
3. Set up your Telegram bot token in environment variables
4. Start the bot using one of the following methods:
   - For development: `python main.py`
   - For 24/7 operation: `./run_forever.py`
   - For server deployment: `./deploy.sh start`

## Installation in Production

For deploying in a production environment:

1. Ensure Python 3.7+ is installed
2. Clone the repository
3. Run `./setup_environment.sh` to install dependencies
4. Create environment variables for `TELEGRAM_TOKEN` and optionally `DEVELOPER_IDS`
5. Use the deployment script: `./deploy.sh start`
6. Monitor the status: `./deploy.sh status`
7. View logs: `./deploy.sh logs`

The bot features automatic recovery from crashes and will maintain 24/7 operation.

## Environment Variables

- `TELEGRAM_TOKEN` - Your Telegram Bot API token
- `DEVELOPER_IDS` - Comma-separated list of developer Telegram user IDs (for admin commands)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.