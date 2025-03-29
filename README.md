# TaskMaster Pro - Telegram Task Management Bot

A powerful Telegram bot designed for comprehensive task management, supporting both individual and collaborative productivity workflows.

## Features

- **Task Management**: Create, list, complete, and delete tasks
- **Advanced Filtering**: View tasks by priority, category, due date (/today, /week)
- **Reminders**: Set automated reminders for your tasks
- **Group Support**: Collaborative task management in group chats
- **Interactive Interface**: User-friendly command system with inline buttons
- **Categories & Tags**: Organize tasks with custom categories and tags
- **Priority Levels**: Set task importance with priority flags
- **Chat Cleaning**: Keep conversations tidy with the /clean command

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
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up your Telegram bot token in environment variables
4. Run the bot: `python main.py`

## Environment Variables

- `TELEGRAM_TOKEN` - Your Telegram Bot API token
- `DEVELOPER_IDS` - Comma-separated list of developer Telegram user IDs (for admin commands)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.