#!/bin/bash

# Go to bot directory
cd ~/Desktop/clean_smm_bot

# Activate the virtual environment
source venv/bin/activate

# Install the missing imghdr module (Python 3.13 compatibility fix)
echo "Installing imghdr compatibility package..."
pip install image-to-header || echo "Failed to install image-to-header, but continuing..."

# Try to patch the python-telegram-bot manually if needed
if [ -f venv/lib/python3.13/site-packages/telegram/files/inputfile.py ]; then
    # Create backup of the original file
    cp venv/lib/python3.13/site-packages/telegram/files/inputfile.py venv/lib/python3.13/site-packages/telegram/files/inputfile.py.bak
    
    # Patch the file to handle missing imghdr
    sed -i '' 's/import imghdr/try:\n    import imghdr\nexcept ImportError:\n    imghdr = None/' venv/lib/python3.13/site-packages/telegram/files/inputfile.py
    
    # Check if we need to patch the usage of imghdr too
    grep -q "imghdr.what" venv/lib/python3.13/site-packages/telegram/files/inputfile.py
    if [ $? -eq 0 ]; then
        # Patch imghdr.what usage
        sed -i '' 's/imghdr.what/imghdr.what if imghdr else None/' venv/lib/python3.13/site-packages/telegram/files/inputfile.py
        echo "Patched imghdr usage in python-telegram-bot"
    fi
    
    echo "Patched python-telegram-bot for Python 3.13 compatibility"
fi

echo "Starting the bot..."
cd bot
python bot.py 