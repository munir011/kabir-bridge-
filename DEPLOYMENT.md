# Deploying Kabir Bridge Bot to EC2

This guide explains how to deploy the Kabir Bridge Telegram Bot to an Amazon EC2 instance.

## Prerequisites

1. An AWS account with EC2 access
2. An EC2 instance running Ubuntu (recommended: t2.micro or larger)
3. SSH access to your EC2 instance
4. A Telegram bot token

## Deployment Steps

### 1. Set Up EC2 Instance

1. Launch an EC2 instance with Ubuntu Server (20.04 LTS or newer)
2. Configure security groups to allow:
   - SSH (port 22) from your IP
   - HTTPS (port 443) for outbound connections to Telegram API

### 2. Clone the Repository

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone the repository
git clone https://github.com/yourusername/kabir-bridge-bot.git
cd kabir-bridge-bot
```

### 3. Set Up the Environment

```bash
# Make the setup script executable
chmod +x ec2_setup.sh

# Run the setup script
./ec2_setup.sh
```

### 4. Configure the Bot

1. Edit the `.env` file in the `bot` directory:
```bash
nano bot/.env
```

2. Update the Telegram bot token and other settings

### 5. Set Up as a Service

```bash
# Copy the service file to systemd
sudo cp kabir-bridge-bot.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable kabir-bridge-bot
sudo systemctl start kabir-bridge-bot

# Check status
sudo systemctl status kabir-bridge-bot
```

### 6. Monitoring and Maintenance

- Check logs: `sudo journalctl -u kabir-bridge-bot`
- Restart the service: `sudo systemctl restart kabir-bridge-bot`
- Stop the service: `sudo systemctl stop kabir-bridge-bot`

## Updating the Bot

To update the bot with new code:

```bash
cd ~/kabir-bridge-bot
git pull
sudo systemctl restart kabir-bridge-bot
```

## Troubleshooting

- If the bot fails to start, check the logs for errors
- Ensure the `.env` file contains the correct bot token
- Verify that Python 3.11 and all dependencies are installed correctly 