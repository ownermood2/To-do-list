#!/bin/bash
# Push all updates to GitHub repository

echo "======================================="
echo "TaskMaster Pro - GitHub Push"
echo "======================================="

# Default repository URL from config
REPO_URL=$(grep -oP 'REPOSITORY_URL = "\K[^"]+' config.py)

# Check if a repository URL is specified
if [ -z "$REPO_URL" ]; then
    echo "ERROR: Repository URL not found in config.py"
    echo "Please set REPOSITORY_URL in config.py or specify manually"
    exit 1
fi

echo "Using repository URL: $REPO_URL"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git and try again."
    exit 1
fi

# Check if the directory is a git repository
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    
    # Add the remote
    echo "Adding remote repository..."
    git remote add origin $REPO_URL
    
    if [ $? -ne 0 ]; then
        echo "Failed to add remote repository. Check if the URL is correct."
        exit 1
    fi
fi

# Check if the remote exists
if ! git remote get-url origin &> /dev/null; then
    echo "Remote 'origin' not found. Adding remote..."
    git remote add origin $REPO_URL
fi

# Get commit message
echo
echo "Enter a commit message (or press Enter for default message):"
read -p "> " COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    # Get the current date and time
    DATETIME=$(date +"%Y-%m-%d %H:%M:%S")
    COMMIT_MESSAGE="TaskMaster Pro updates - $DATETIME"
    echo "Using default commit message: '$COMMIT_MESSAGE'"
fi

# Stage all files
echo
echo "Staging all files..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "$COMMIT_MESSAGE"

# Push to GitHub
echo
echo "Pushing to GitHub..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo
    echo "✓ Successfully pushed all updates to GitHub!"
    echo "Repository URL: $REPO_URL"
else
    echo
    echo "× Failed to push to GitHub. You may need to:"
    echo "  1. Ensure you have the correct access permissions"
    echo "  2. Try 'git pull' to update your local repository first"
    echo "  3. Fix any merge conflicts if they exist"
fi