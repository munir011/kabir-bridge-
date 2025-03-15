#!/bin/bash

# Go to the script's directory to ensure we're in the right place
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Make sure the data directory exists
mkdir -p data

# Copy the .env file from the root to the bot directory if it doesn't exist
if [ -f ".env" ] && [ ! -f "bot/.env" ]; then
    echo "Copying .env file to bot directory..."
    cp .env bot/.env
fi

# Set up Python environment
if [ -d "venv" ]; then
    echo "Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run the bot
echo "Starting the bot..."
cd bot
python bot.py

# If the bot stops, keep the window open
echo "Bot has stopped. Press any key to exit."
read -n 1 -s

# Note: To run this script, use: ./run_bot.sh