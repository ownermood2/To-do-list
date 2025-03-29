#!/usr/bin/env python
"""
Test script for enhanced time parsing in TaskMaster Pro
"""
from utils import parse_time
from datetime import datetime

test_times = [
    'tomorrow 3pm',
    'friday 10am',
    '15:30',
    'apr 15',
    '1h 30m',
    '2 hours',
    '3:45',
    'mon 9am',
    'may 20 2pm',
    '10pm'
]

def main():
    """Test various time formats with the enhanced parser"""
    print('Current time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    for t in test_times:
        result = parse_time(t)
        if result:
            print(f'Testing "{t}": {datetime.fromtimestamp(result).strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            print(f'Testing "{t}": Failed to parse')

if __name__ == "__main__":
    main()