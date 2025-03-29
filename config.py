import os

# Bot token from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Developer user IDs (for admin commands)
DEVELOPER_IDS = [int(id) for id in os.environ.get("DEVELOPER_IDS", "").split(",") if id]

# Commands
COMMANDS = {
    'start': '🚀 Get started with TaskMaster Pro',
    'help': '📚 Display comprehensive help and tips',
    'add': '➕ Create a new task with options',
    'list': '📋 View your personalized task dashboard',
    'done': '✅ Mark tasks as completed',
    'delete': '🗑️ Remove a task permanently',
    'clear': '🧹 Clear all completed tasks',
    'remind': '⏰ Set smart reminders for tasks',
    'settings': '⚙️ Customize your experience',
    'today': '📆 Show tasks due today',
    'week': '📅 Show tasks due this week',
    'priority': '🔝 Set task priority levels',
    'stats': '📊 View your productivity statistics',
    'join': '🔗 Join a group via invite link',
    'tag': '🏷️ Add labels and categories to tasks',
    'search': '🔍 Find specific tasks',
    'export': '📤 Export your tasks',
}

# Developer commands (hidden from regular users)
DEVELOPER_COMMANDS = {
    'broadcast': 'Send announcement to all users',
    'devstats': 'Show detailed bot statistics',
    'maintenance': 'Enable/disable maintenance mode',
    'debug': 'Show debug information',
}

# Default messages
WELCOME_MESSAGE = (
    "✨ *Welcome to TaskMaster Pro* ✨\n\n"
    "Your personal productivity assistant is here! I'll help you organize your life, track your goals, and boost your productivity.\n\n"
    "*Key Features:*\n"
    "📌 Create and manage tasks with smart reminders\n"
    "🏷️ Categorize and prioritize with powerful organization tools\n"
    "📊 Track your productivity with detailed statistics\n"
    "🔍 Find exactly what you need with advanced filtering\n"
    "🔄 Seamless integration with groups and teams\n"
    "⏰ Never miss deadlines with intelligent notifications\n\n"
    "*Quick Start Commands:*\n"
    "• /add - Create a new task with optional deadline and priority\n"
    "• /list - View your personalized task dashboard\n"
    "• /today - See only tasks due today\n"
    "• /priority - Set importance levels for better focus\n"
    "• /tag - Organize tasks by category\n"
    "• /help - Discover all powerful features\n\n"
    "💡 *Pro Tip:* Simply send me a group invitation link to add me to your team chats and enhance collaboration!"
)

HELP_MESSAGE = (
    "🌟 *TaskMaster Pro - Command Center* 🌟\n\n"
    "Discover the full power of your productivity assistant:\n\n"
    "*Task Management:*\n"
    "• /add - Create tasks with optional deadlines, priorities, and categories\n"
    "• /list - View your personalized task dashboard\n"
    "• /done - Mark tasks as completed to track your progress\n"
    "• /delete - Remove tasks you no longer need\n"
    "• /clear - Clean up your task list by removing all completed tasks\n\n"
    
    "*Organization & Filtering:*\n"
    "• /today - See only tasks due today for immediate focus\n"
    "• /week - View your upcoming week for better planning\n"
    "• /priority - Set High/Medium/Low priorities for better task management\n"
    "• /tag - Categorize tasks (Work, Personal, Shopping, etc.)\n"
    "• /search - Find specific tasks by keyword\n\n"
    
    "*Productivity Features:*\n"
    "• /remind - Set reminders so you never miss a deadline\n"
    "• /stats - View your productivity metrics and completion rate\n"
    "• /settings - Customize notification preferences and categories\n\n"
    
    "*Group Collaboration:*\n"
    "• /join - Add this bot to your groups via invitation link\n"
    "• All commands work in groups for team task management\n\n"
    
    "💡 *Pro Tip:* You can simply send a group invitation link directly to the bot to add it to your groups!"
)

GROUP_WELCOME_MESSAGE = (
    "✨ *TaskMaster Pro has joined the team!* ✨\n\n"
    "Hello everyone! I'm your group's new productivity powerhouse.\n\n"
    "*Team Productivity Features:*\n"
    "📌 Create shared tasks visible to all members\n"
    "📊 Track team progress and contributions\n"
    "🔔 Get synchronized reminders for deadlines\n"
    "🔄 Seamless coordination for group projects\n"
    "🏷️ Categorize and prioritize team tasks\n\n"
    "*Quick Start Commands:*\n"
    "• /add - Create a new task for the team\n"
    "• /list - View the group's shared task dashboard\n"
    "• /done - Mark team tasks as completed\n"
    "• /priority - Set High/Medium/Low priorities\n"
    "• /tag - Categorize tasks by project or department\n"
    "• /today - See tasks due today for your team\n"
    "• /week - View upcoming tasks for better planning\n"
    "• /help - Discover all team productivity features\n\n"
    "💡 *Pro Tip:* Use @mentions in tasks to assign responsibilities to specific team members!"
)

# File path for storing data
DATA_FILE = "todo_data.json"

# Reminder check interval (in seconds)
REMINDER_CHECK_INTERVAL = 60
