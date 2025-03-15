#!/bin/bash

# Configuration - EDIT THESE VALUES
EC2_USER="ubuntu"
EC2_IP="your-ec2-ip"  # Replace with your EC2 instance's public IP
KEY_PATH="$HOME/.ssh/your-key.pem"  # Replace with the path to your .pem file

# Check if key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH key file not found at $KEY_PATH"
    echo "Please update the KEY_PATH variable in this script."
    exit 1
fi

# Make sure the key has the right permissions
chmod 400 "$KEY_PATH"

# Connect to EC2 and check bot status
echo "Checking Kabir Bridge Bot status on EC2..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'EOF'
    echo "=== Bot Service Status ==="
    sudo systemctl status kabir-bridge-bot --no-pager
    
    echo -e "\n=== Recent Logs ==="
    sudo journalctl -u kabir-bridge-bot -n 20 --no-pager
    
    echo -e "\n=== System Resources ==="
    echo "Memory Usage:"
    free -h
    
    echo -e "\nDisk Usage:"
    df -h | grep -v tmpfs
    
    echo -e "\nCPU Load:"
    uptime
EOF

echo "Status check completed!" 