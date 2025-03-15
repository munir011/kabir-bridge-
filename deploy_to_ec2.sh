#!/bin/bash

# Kabir Bridge Bot EC2 Deployment Script
echo "Deploying Kabir Bridge Bot to EC2..."

# Configuration - EDIT THESE VALUES
EC2_USER="ec2-user"
EC2_IP="your-ec2-public-dns.amazonaws.com"  # Replace with your EC2 instance's public DNS
KEY_PATH="$HOME/path/to/your-key.pem"  # Replace with the path to your .pem file
REPO_URL="https://github.com/munir011/kabir-bridge-.git"
BOT_DIR="kabir-bridge-bot"

# Check if key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH key file not found at $KEY_PATH"
    echo "Please update the KEY_PATH variable in this script."
    exit 1
fi

# Make sure the key has the right permissions
chmod 400 "$KEY_PATH"

# Connect to EC2 and set up the environment
echo "Connecting to EC2 instance and setting up the environment..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'EOF'
    # Update system packages
    sudo yum update -y

    # Install Python 3.11 and required packages
    echo "Installing Python 3.11 and dependencies..."
    sudo yum install -y python3.11 python3.11-devel python3.11-pip git

    # Clone the repository
    echo "Cloning the repository..."
    if [ -d "$BOT_DIR" ]; then
        echo "Directory already exists, pulling latest changes..."
        cd "$BOT_DIR"
        git pull
    else
        git clone "$REPO_URL" "$BOT_DIR"
        cd "$BOT_DIR"
    fi

    # Create and activate virtual environment
    echo "Setting up Python virtual environment..."
    python3.11 -m venv venv_py311
    source venv_py311/bin/activate

    # Install dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt

    # Set up the systemd service
    echo "Setting up systemd service..."
    sudo cp kabir-bridge-bot.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable kabir-bridge-bot
    
    # Start the service
    echo "Starting the bot service..."
    sudo systemctl restart kabir-bridge-bot
    
    # Check service status
    echo "Service status:"
    sudo systemctl status kabir-bridge-bot --no-pager
EOF

echo "Deployment completed!"
echo "To check logs: ssh -i $KEY_PATH $EC2_USER@$EC2_IP 'sudo journalctl -u kabir-bridge-bot'"
echo "To restart the bot: ssh -i $KEY_PATH $EC2_USER@$EC2_IP 'sudo systemctl restart kabir-bridge-bot'" 