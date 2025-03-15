#!/bin/bash

# Go to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Copy .env file to bot directory
if [ -f ".env" ]; then
    echo "Copying .env file to bot directory..."
    cp .env bot/.env
else
    echo "Warning: .env file not found in root directory!"
    echo "Please create a .env file with your configuration before running the bot."
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Make run script executable
chmod +x run_bot.sh

echo ""
echo "Installation complete!"
echo "To run the bot, use: ./run_bot.sh"
echo "" 