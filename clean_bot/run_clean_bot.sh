#!/bin/bash

# Set up Python environment
if [ -d ".venv" ]; then
    echo "Activating existing virtual environment..."
    source .venv/bin/activate
else
    echo "Creating new virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Make sure the data directory exists
mkdir -p data

# Run the bot
cd bot
python bot.py

# Keep the window open after the bot stops
echo "Bot has stopped. Press Ctrl+C to exit."
read -r 