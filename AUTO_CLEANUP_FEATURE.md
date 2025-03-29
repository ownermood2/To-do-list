# Automatic Chat Cleanup Feature

## Overview

This document describes the automatic chat cleanup feature implemented in TaskMaster Pro, which helps keep group chats tidy by automatically removing old bot messages.

## Implementation Details

### Settings

The feature allows users to customize the following settings:

- **Auto-Clean Enable/Disable**: Users can toggle the automatic cleaning feature on or off for each chat.
- **Retention Period**: Users can select how long bot messages should be kept before cleanup:
  - 3 days (Quick cleanup - good for active groups)
  - 7 days (Standard - default setting)
  - 14 days (Extended history)
  - 30 days (Maximum retention)

### Configuration

Settings are accessible through the `/settings` command in the Telegram bot. Each chat can have its own independent settings.

### Components

1. **Database Support**: 
   - Added chat-specific settings for auto-clean preferences
   - Settings are stored in the JSON database with the chat data

2. **Settings UI**:
   - Added auto-clean toggle button
   - Added retention period selection
   - Added help information for each setting

3. **Cleanup Logic**:
   - Enhanced the `auto_cleanup.py` script to use chat-specific settings
   - Added respect for the auto-clean enable/disable setting
   - Implemented chat-specific retention period handling

4. **Scheduling**:
   - Set to run automatically once per day (at 3:00 AM UTC)
   - Can be manually triggered via the `./run_cleanup.sh` script

5. **User Interface Enhancements**:
   - Added detailed help information for each setting
   - Implemented settings keyboard with help buttons

## Usage

### Automatic Execution

The cleanup process runs automatically once per day. It:
1. Checks each group chat's settings
2. Skips chats that have disabled auto-clean
3. Uses the appropriate retention period for each chat
4. Deletes messages older than the specified period
5. Updates the message database to remove deleted messages

### Manual Testing

For testing or manual execution:

```bash
# Run with default settings
./run_cleanup.sh

# Run with custom default days
./run_cleanup.sh --days 14

# Run with debug information
./run_cleanup.sh --debug
```

## Files Modified

- `handlers.py`: Added handlers for auto-clean settings
- `keyboards.py`: Updated settings keyboard to include auto-clean options
- `auto_cleanup.py`: Enhanced to respect chat-specific settings
- `main.py`: Updated to use new auto-cleanup parameters
- `test_cleanup.py`: Added for manual testing
- `run_cleanup.sh`: Added shell script for easy testing

## Future Enhancements

Potential improvements for future updates:
- Add per-command cleanup settings (e.g., keep /list messages longer than others)
- Implement time-of-day settings for when cleanup should occur
- Add notification options for when cleanups are performed
- Create more granular retention periods