#!/bin/bash

# Uninstall conflicting packages
pip uninstall -y telegram python-telegram-bot

# Install the specific version of python-telegram-bot
pip install python-telegram-bot==13.7

echo "Environment setup complete!"