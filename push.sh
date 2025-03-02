#!/bin/bash

# Get current timestamp for backup files
timestamp=$(date "+%Y%m%d_%H%M%S")

# Get list of modified files
changed_files=$(git status --porcelain | awk '{print $2}')

# Backup each changed file
for file in $changed_files; do
    if [ -f "$file" ]; then
        backup_path="backups/$(basename "$file").${timestamp}.bak"
        cp "$file" "$backup_path"
        echo "Backed up: $file -> $backup_path"
    fi
done

# Proceed with git commands
git init
git status
git add -f .
git commit -m "update"
# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    git remote add origin $REMOTE_ADD_ORIGIN
else
    echo "Error: .env file not found"
    exit 1
fi
git push -f origin main