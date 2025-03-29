from telegram.ext import CommandHandler
from typing import Dict, List, Callable, Any

# Basic commands for all users
USER_COMMANDS = {
    'start': {
        'description': 'Start using the bot',
        'help': 'Initializes the bot for your personal or group use'
    },
    'help': {
        'description': 'Show available commands',
        'help': 'Displays a list of all available commands with descriptions'
    },
    'add': {
        'description': 'Add a new task',
        'help': 'Add a new task to your to-do list\nUsage: /add Buy groceries'
    },
    'list': {
        'description': 'List all tasks',
        'help': 'Show all your active tasks'
    },
    'done': {
        'description': 'Mark a task as done',
        'help': 'Mark a task as completed\nUsage: /done 1'
    },
    'delete': {
        'description': 'Delete a task',
        'help': 'Delete a task from your list\nUsage: /delete 1'
    },
    'clear': {
        'description': 'Clear all tasks',
        'help': 'Delete all tasks from your list (requires confirmation)'
    },
    'remind': {
        'description': 'Set a reminder for a task',
        'help': 'Set a reminder for a specific task\nUsage: /remind 1 30m'
    },
    'settings': {
        'description': 'Configure bot settings',
        'help': 'Adjust your personal settings for the bot'
    }
}

# Developer commands (hidden from regular users)
DEVELOPER_COMMANDS = {
    'broadcast': {
        'description': 'Send announcement to all users',
        'help': 'Send a message to all users and groups\nUsage: /broadcast Your message here'
    },
    'stats': {
        'description': 'Show bot statistics',
        'help': 'Display usage statistics for the bot'
    },
    'maintenance': {
        'description': 'Enable/disable maintenance mode',
        'help': 'Toggle maintenance mode (disables commands for regular users)'
    },
    'debug': {
        'description': 'Show debug information',
        'help': 'Display technical debug information about the current chat'
    }
}

def get_command_help(command: str, is_developer: bool = False) -> str:
    """Get detailed help for a specific command"""
    if command in USER_COMMANDS:
        return f"/{command} - {USER_COMMANDS[command]['description']}\n\n{USER_COMMANDS[command]['help']}"
    elif is_developer and command in DEVELOPER_COMMANDS:
        return f"/{command} - {DEVELOPER_COMMANDS[command]['description']}\n\n{DEVELOPER_COMMANDS[command]['help']}"
    else:
        return f"Command not found: {command}"

def get_all_commands_help(is_developer: bool = False) -> str:
    """Get help text for all commands"""
    help_text = "📋 *Available Commands*:\n\n"
    
    # Add user commands
    for cmd, info in USER_COMMANDS.items():
        help_text += f"/{cmd} - {info['description']}\n"
    
    # Add developer commands if applicable
    if is_developer:
        help_text += "\n🛠️ *Developer Commands*:\n\n"
        for cmd, info in DEVELOPER_COMMANDS.items():
            help_text += f"/{cmd} - {info['description']}\n"
    
    return help_text

def register_commands(
    application: Any, 
    handlers: Dict[str, Callable]
) -> None:
    """Register all command handlers with the application"""
    # Register user commands
    for command in USER_COMMANDS:
        if command in handlers:
            application.add_handler(CommandHandler(command, handlers[command]))
    
    # Register developer commands
    for command in DEVELOPER_COMMANDS:
        if command in handlers:
            application.add_handler(CommandHandler(command, handlers[command]))
