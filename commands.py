from telegram.ext import CommandHandler
from typing import Dict, List, Callable, Any

# Basic commands for all users
USER_COMMANDS = {
    'start': {
        'description': '🚀 Get started with TaskMaster Pro',
        'help': 'Initializes the bot for your personal or group use and shows welcome information'
    },
    'help': {
        'description': '📚 Display comprehensive help and tips',
        'help': 'Displays a list of all available commands with detailed descriptions'
    },
    'add': {
        'description': '➕ Create a new task with options',
        'help': 'Add a new task to your to-do list\nUsage: /add Buy groceries'
    },
    'list': {
        'description': '📋 View your personalized task dashboard',
        'help': 'Show all your active tasks with options to manage them'
    },
    'done': {
        'description': '✅ Mark tasks as completed',
        'help': 'Mark a task as completed\nUsage: /done 1'
    },
    'delete': {
        'description': '🗑️ Remove a task permanently',
        'help': 'Delete a task from your list\nUsage: /delete 1'
    },
    'clear': {
        'description': '🧹 Clear all completed tasks',
        'help': 'Delete all tasks from your list (requires confirmation)'
    },
    'remind': {
        'description': '⏰ Set smart reminders for tasks',
        'help': 'Set a reminder for a specific task\nUsage: /remind 1 30m'
    },
    'settings': {
        'description': '⚙️ Customize your experience',
        'help': 'Adjust your personal settings for the bot'
    },
    'join': {
        'description': '🔗 Join a group via invite link',
        'help': 'Invite the bot to a group chat using an invite link\nUsage: /join https://t.me/joinchat/AbCdEfGh'
    },
    'today': {
        'description': '📆 Show tasks due today',
        'help': 'View all tasks that are due today'
    },
    'week': {
        'description': '📅 Show tasks due this week',
        'help': 'View all tasks that are due within the next 7 days'
    },
    'priority': {
        'description': '🔝 Set task priority levels',
        'help': 'Set or change priority level for a task\nUsage: /priority 1 high'
    },
    'stats': {
        'description': '📊 View your productivity statistics',
        'help': 'Check your task completion statistics and productivity metrics'
    },
    'tag': {
        'description': '🏷️ Add labels and categories to tasks',
        'help': 'Add categories or tags to organize your tasks\nUsage: /tag 1 Work'
    },
    'search': {
        'description': '🔍 Find specific tasks',
        'help': 'Search through your tasks by keyword\nUsage: /search grocery'
    },
    'clean': {
        'description': '🧽 Clean up conversation history',
        'help': 'Remove bot messages from chat to keep it organized (group-friendly feature)'
    }
}

# Developer commands (hidden from regular users)
DEVELOPER_COMMANDS = {
    'broadcast': {
        'description': 'Send announcement to all users',
        'help': 'Send a message to all users and groups\nUsage: /broadcast Your message here'
    },
    'groupcast': {
        'description': 'Send announcement to a specific group',
        'help': 'Send a message to a specific group chat\nUsage options:\n• `/groupcast GROUP_ID Your message here`\n• `/groupcast @group_username Your message here`\n• `/groupcast group_username Your message here`'
    },
    'delbroadcast': {
        'description': 'Delete a broadcast from all chats',
        'help': 'Delete a previously sent broadcast message from all chats\nUsage: /delbroadcast BROADCAST_ID\n\nUse without an ID to see recent broadcasts.'
    },
    'devstats': {
        'description': 'Show detailed bot statistics',
        'help': 'Display comprehensive usage statistics for the bot'
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
