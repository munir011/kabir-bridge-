#!/bin/bash

# Define the target directory for the clean SMM Bot
TARGET_DIR="$HOME/Desktop/SMM_Bot_Clean"

# Create fresh directory
echo "Creating clean directory at $TARGET_DIR..."
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/bot"
mkdir -p "$TARGET_DIR/data"

# Copy only the essential files
echo "Copying essential files..."

# 1. Copy bot code
if [ -d ~/Desktop/clean_smm_bot/bot ]; then
    echo "Copying bot code..."
    cp -r ~/Desktop/clean_smm_bot/bot/* "$TARGET_DIR/bot/"
fi

# 2. Copy .env file
if [ -f ~/Desktop/clean_smm_bot/.env ]; then
    echo "Copying .env file..."
    cp ~/Desktop/clean_smm_bot/.env "$TARGET_DIR/"
    cp ~/Desktop/clean_smm_bot/.env "$TARGET_DIR/bot/"
fi

# 3. Copy requirements.txt
if [ -f ~/Desktop/clean_smm_bot/requirements.txt ]; then
    echo "Copying requirements.txt..."
    cp ~/Desktop/clean_smm_bot/requirements.txt "$TARGET_DIR/"
fi

# 4. Copy database file if it exists
if [ -f ~/Desktop/clean_smm_bot/data/smm_bot.db ]; then
    echo "Copying database file..."
    cp ~/Desktop/clean_smm_bot/data/smm_bot.db "$TARGET_DIR/data/"
fi

# 5. Copy README file
if [ -f README.md ]; then
    echo "Copying README file..."
    cp README.md "$TARGET_DIR/"
fi

# Create run script
echo "Creating run script..."
cat > "$TARGET_DIR/run.sh" << 'EOF'
#!/bin/bash

# Go to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Fix for Python 3.13 imghdr issue
    if [ -f venv/lib/python*/site-packages/telegram/files/inputfile.py ]; then
        echo "Applying compatibility patch for Telegram..."
        # Create backup of the original file
        cp venv/lib/python*/site-packages/telegram/files/inputfile.py venv/lib/python*/site-packages/telegram/files/inputfile.py.bak
        
        # Patch the file to handle missing imghdr
        sed -i '' 's/import imghdr/try:\n    import imghdr\nexcept ImportError:\n    imghdr = None/' venv/lib/python*/site-packages/telegram/files/inputfile.py
        
        # Patch imghdr.what usage
        sed -i '' 's/imghdr\.what/imghdr.what if imghdr else None/g' venv/lib/python*/site-packages/telegram/files/inputfile.py
    fi
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

# Make sure data directory exists
mkdir -p data

# Run the bot
echo "Starting SMM Panel Bot..."
cd bot
python bot.py
EOF

# Make run script executable
chmod +x "$TARGET_DIR/run.sh"

# Create a launcher in home directory
echo "Creating launcher in home directory..."
cat > "$HOME/run_smm_bot.sh" << 'EOF'
#!/bin/bash

# Go to the clean bot directory
cd "$HOME/Desktop/SMM_Bot_Clean"

# Run the bot
./run.sh
EOF

# Make launcher executable
chmod +x "$HOME/run_smm_bot.sh"

echo "==================================================="
echo "✅ Cleanup complete! All unnecessary files removed."
echo "==================================================="
echo ""
echo "Your clean SMM Bot is now at: $TARGET_DIR"
echo ""
echo "To run your bot:"
echo "Option 1: From any directory"
echo "  ~/run_smm_bot.sh"
echo ""
echo "Option 2: From the bot directory"
echo "  cd $TARGET_DIR"
echo "  ./run.sh"
echo ""
echo "Before running, make sure to check your .env file:"
echo "  nano $TARGET_DIR/.env"
echo "==================================================="

# Ask if user wants to remove the old directories
read -p "Do you want to remove the old directories? (y/n): " choice
case "$choice" in 
  y|Y ) 
    echo "Removing old directories..."
    rm -rf ~/Desktop/clean_smm_bot
    rm -rf ~/Desktop/tutrial
    echo "Old directories removed."
    ;;
  * ) 
    echo "Old directories kept."
    ;;
esac 