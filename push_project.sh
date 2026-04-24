#!/bin/bash
# Ensure we are in a git repo
git init
# Set the remote (uses the authenticated URL from .git/config if already set)
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Black-synapse-CU/rpi_emotion.git
# Stage and commit
git add .
git commit -m "Initial commit: Raspberry Pi Emotion Recognition project"
# Push
git push -u origin main
