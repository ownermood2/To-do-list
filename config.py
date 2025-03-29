import os

# Bot token from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Developer user IDs (for admin commands)
DEVELOPER_IDS = [int(id) for id in os.environ.get("DEVELOPER_IDS", "").split(",") if id]

# Commands
COMMANDS = {
    'start': 'Start using the bot',
    'help': 'Show available commands',
    'add': 'Add a new task',
    'list': 'List all tasks',
    'done': 'Mark a task as done',
    'delete': 'Delete a task',
    'clear': 'Clear all tasks',
    'remind': 'Set a reminder for a task',
    'settings': 'Configure bot settings',
}

# Developer commands (hidden from regular users)
DEVELOPER_COMMANDS = {
    'broadcast': 'Send announcement to all users',
    'stats': 'Show bot statistics',
    'maintenance': 'Enable/disable maintenance mode',
    'debug': 'Show debug information',
}

# Default messages
WELCOME_MESSAGE = (
    "👋 Welcome to *Todo List Bot*!\n\n"
    "I'll help you manage your tasks and to-do lists both for personal use and in groups.\n\n"
    "Here are some things you can do:\n"
    "• Use /add to create a new task\n"
    "• Use /list to see all your tasks\n"
    "• Use /done to mark tasks as completed\n"
    "• Use /help to see all available commands"
)

HELP_MESSAGE = "Here are all available commands:\n\n"

GROUP_WELCOME_MESSAGE = (
    "👋 Hello everyone! I'm *Todo List Bot*!\n\n"
    "I'll help this group manage tasks and to-do lists.\n\n"
    "Here are some things you can do:\n"
    "• Use /add to create a new task\n"
    "• Use /list to see all group tasks\n"
    "• Use /done to mark tasks as completed\n"
    "• Use /help to see all available commands"
)

# File path for storing data
DATA_FILE = "todo_data.json"

# Reminder check interval (in seconds)
REMINDER_CHECK_INTERVAL = 60
