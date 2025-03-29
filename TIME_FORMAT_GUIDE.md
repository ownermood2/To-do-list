# TaskMaster Pro: Time Format Guide

TaskMaster Pro now supports a wide variety of time and date formats for setting reminders! This guide explains all the formats available to you.

## Time Format Options

When using the `/remind` command or setting up a custom reminder, you can specify time in many different ways:

### Relative Time (from now)

| Format | Examples | Description |
|--------|----------|-------------|
| Short format | `1h 30m`, `5h`, `45m` | Hours and minutes from now |
| Long format | `2 hours 15 minutes`, `1 hour`, `30 minutes` | Hours and minutes from now, spelled out |
| Colon format | `1:30`, `0:45`, `2:00` | Hours:minutes from now |

### Days and Times

| Format | Examples | Description |
|--------|----------|-------------|
| Today | `today 3pm`, `today 15:00` | Later today at the specified time |
| Tomorrow | `tomorrow 9am`, `tomorrow 14:30` | Tomorrow at the specified time |
| Day of week | `monday 10am`, `fri 16:00`, `wed 9:30pm` | Next occurrence of that day at the specified time |

### Specific Dates

| Format | Examples | Description |
|--------|----------|-------------|
| Month/Day | `4/20`, `12/25` | MM/DD this year |
| Month-Day | `4-20`, `12-25` | MM-DD this year |
| Month name | `apr 15`, `december 25` | Month name and day |
| With year | `4/20/2025`, `apr 15, 2025` | Full date with year |
| Date with time | `4/20 3pm`, `dec 25 9:00` | Date with specific time |

### Time of Day

| Format | Examples | Description |
|--------|----------|-------------|
| 12-hour | `3pm`, `9:30am`, `12pm` | 12-hour format with am/pm |
| 24-hour | `15:00`, `09:30`, `23:45` | 24-hour format (HH:MM) |
| Hours only | `3` (for 3:00), `15` (for 15:00) | Just the hour (minutes = 00) |
| European style | `15h`, `9h30` | Hours with 'h' format |

## Examples in Action

1. `/remind buy groceries tomorrow 5pm`
   * Sets a reminder for 5:00 PM tomorrow

2. `/remind call mom fri 10am`
   * Sets a reminder for 10:00 AM next Friday

3. `/remind pay bills 3d 12h`
   * Sets a reminder for 3 days and 12 hours from now

4. `/remind dentist appointment apr 15 2pm`
   * Sets a reminder for April 15th at 2:00 PM

5. `/remind take medicine today 8pm`
   * Sets a reminder for 8:00 PM today

## Notes

- If you specify just a time (like "3pm") and it's already past that time today, the reminder will be set for tomorrow.
- If you specify a day of the week that matches today, and the time has already passed, the reminder will be set for next week.
- Dates without years assume the current year, unless the date has already passed, in which case it assumes next year.
- You can use abbreviations for days (mon, tue, wed) and months (jan, feb, mar).

## Troubleshooting

If the bot doesn't understand your time format, try one of these simpler formats:
- `1h 30m` (1 hour and 30 minutes from now)
- `tomorrow 9am` (tomorrow at 9:00 AM)
- `friday 3pm` (next Friday at 3:00 PM)