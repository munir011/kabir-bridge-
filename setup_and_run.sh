#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv311" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv311
fi

# Activate the virtual environment
source .venv311/bin/activate

# Install required packages from requirements.txt
echo "Installing dependencies..."
pip install -r requirements.txt

# Make sure the database directory exists
mkdir -p bot/data

# Run the bot
echo "Starting the bot..."
cd bot
PYTHONPATH=$(pwd) python bot.py 