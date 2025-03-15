#!/bin/bash

# This script creates a new virtual environment using Python 3.11 
# which includes the imghdr module needed by python-telegram-bot

# Go to bot directory
cd ~/Desktop/clean_smm_bot

echo "Checking for Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Installing via Homebrew..."
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew or Python 3.11 manually."
        exit 1
    fi
    
    # Install Python 3.11 using Homebrew
    brew install python@3.11
fi

# Remove old virtual environment
echo "Removing old virtual environment..."
rm -rf venv

# Create new virtual environment with Python 3.11
echo "Creating new virtual environment with Python 3.11..."
python3.11 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! Python 3.11 virtual environment is ready."
echo "Now you can run the bot with: ~/fix_and_run.sh" 