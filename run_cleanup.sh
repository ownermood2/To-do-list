#!/bin/bash
# Script to run the auto-cleanup test

echo "Running auto-cleanup test..."

# Run the cleanup test with default settings
python test_cleanup.py "$@"

echo "Cleanup test complete. Check test_cleanup.log for details."