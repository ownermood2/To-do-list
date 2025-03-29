#!/bin/bash

# Script to push updates to GitHub
echo "=== TaskMaster Pro GitHub Update ==="
echo "Pushing updates to GitHub repository..."

# Configure Git (adjust these as needed)
git config --global user.email "bot@taskmaster-pro.com"
git config --global user.name "TaskMaster Pro Bot"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
fi

# Check if the remote repository exists
if ! git remote | grep -q origin; then
    echo "Adding GitHub remote..."
    git remote add origin https://github.com/ownermood2/To-do-list.git
fi

# Add all changes
echo "Adding changes to Git..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Update TaskMaster Pro - Fix group joining and edited message handling"

# Push changes to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "=== All updates pushed to GitHub ==="