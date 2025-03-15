#!/bin/bash

# EC2 Setup Script for Kabir Bridge Bot
echo "Setting up Kabir Bridge Bot on EC2..."

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11 and required packages
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip git

# Create and activate virtual environment
python3.11 -m venv venv_py311
source venv_py311/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up the bot
echo "Bot setup complete. Run ./start.sh to start the bot." 