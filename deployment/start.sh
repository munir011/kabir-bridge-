#!/bin/bash

# Kabir Bridge Bot EC2 Starter Script
echo "Starting Kabir Bridge Bot on EC2..."

# Navigate to the bot directory
cd "$(dirname "$0")/bot"

# Activate the virtual environment
source ../venv_py311/bin/activate

# Run the bot
python bot.py

# This line will only execute if the bot stops
echo "Bot has stopped. To restart, run this script again." 