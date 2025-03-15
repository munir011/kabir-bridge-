# Manual EC2 Deployment Guide for Kabir Bridge Bot

This guide provides step-by-step instructions for manually deploying the Kabir Bridge Bot to an Amazon EC2 instance.

## Prerequisites

1. An EC2 instance running Amazon Linux 2023 or Ubuntu
2. SSH access to your EC2 instance
3. Your GitHub repository with the bot code

## Step 1: Connect to Your EC2 Instance

```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-ip
```

Replace `/path/to/your-key.pem` with the actual path to your key file and `your-ec2-ip` with your EC2 instance's public IP address.

## Step 2: Install Required Software

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11 and other dependencies
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip git
```

## Step 3: Clone Your Repository

```bash
# Clone the repository
git clone https://github.com/munir011/kabir-bridge-.git kabir-bridge-bot
cd kabir-bridge-bot
```

## Step 4: Set Up Python Environment

```bash
# Create and activate virtual environment
python3.11 -m venv venv_py311
source venv_py311/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Configure the Bot

```bash
# Create or edit the .env file
nano bot/.env
```

Add the following content (replace with your actual values):

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_telegram_user_id
```

## Step 6: Set Up as a Service

```bash
# Copy the service file to systemd
sudo cp kabir-bridge-bot.service /etc/systemd/system/

# Edit the service file if needed
sudo nano /etc/systemd/system/kabir-bridge-bot.service
```

Make sure the paths in the service file match your actual setup:

```
[Unit]
Description=Kabir Bridge Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kabir-bridge-bot
ExecStart=/bin/bash -c 'source /home/ubuntu/kabir-bridge-bot/venv_py311/bin/activate && python /home/ubuntu/kabir-bridge-bot/bot/bot.py'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Step 7: Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable kabir-bridge-bot

# Start the service
sudo systemctl start kabir-bridge-bot

# Check the status
sudo systemctl status kabir-bridge-bot
```

## Step 8: Monitor and Maintain

### Check Logs
```bash
sudo journalctl -u kabir-bridge-bot
```

### Restart the Bot
```bash
sudo systemctl restart kabir-bridge-bot
```

### Stop the Bot
```bash
sudo systemctl stop kabir-bridge-bot
```

## Updating the Bot

When you update your code on GitHub, you can update the bot on EC2:

```bash
cd ~/kabir-bridge-bot
git pull
sudo systemctl restart kabir-bridge-bot
```

## Troubleshooting

### Service Fails to Start
1. Check the logs: `sudo journalctl -u kabir-bridge-bot`
2. Verify the .env file has the correct bot token
3. Make sure all paths in the service file are correct
4. Check Python dependencies are installed: `pip list`

### Python Command Not Found
If you see "python: command not found", make sure to use `python3.11` instead of `python` or update the service file to use the full path to Python.

### Permission Issues
If you encounter permission issues, make sure the ubuntu user has access to all necessary files:
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/kabir-bridge-bot
``` 