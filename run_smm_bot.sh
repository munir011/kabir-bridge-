#!/bin/bash

# Define the correct directory where the bot is installed
BOT_DIR="$HOME/Desktop/clean_smm_bot"

# Check if the directory exists
if [ ! -d "$BOT_DIR" ]; then
    echo "Error: Bot directory not found at $BOT_DIR"
    echo "Please run the cleanup_and_setup.sh script first."
    exit 1
fi

# Navigate to the bot directory
cd "$BOT_DIR"

# Check if the run script exists
if [ ! -f "run_bot.sh" ]; then
    echo "Error: run_bot.sh not found in $BOT_DIR"
    echo "The bot files may be corrupted. Please run cleanup_and_setup.sh again."
    exit 1
fi

# Make sure the script is executable
chmod +x run_bot.sh

# Run the bot
./run_bot.sh

# Note: To use this script, just run it from anywhere with: ./run_smm_bot.sh 