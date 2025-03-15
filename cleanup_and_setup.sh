#!/bin/bash

# Define the target directory
TARGET_DIR="$HOME/Desktop/clean_smm_bot"

# Create the target directory if it doesn't exist
echo "Creating directory at $TARGET_DIR..."
mkdir -p "$TARGET_DIR"

# Copy the clean bot files to the target directory
echo "Copying files to $TARGET_DIR..."
cp -r clean_bot/* "$TARGET_DIR/"

# Make the scripts executable
echo "Setting permissions..."
chmod +x "$TARGET_DIR/run_bot.sh"
chmod +x "$TARGET_DIR/install.sh"

# Create a launcher script in the home directory
echo "Creating launcher script in home directory..."
cat > "$HOME/run_smm_bot.sh" << 'EOF'
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
EOF

# Make the launcher executable
chmod +x "$HOME/run_smm_bot.sh"

echo "---------------------------------------------"
echo "✅ Setup completed successfully!"
echo "---------------------------------------------"
echo ""
echo "The SMM Panel Bot is now set up at: $TARGET_DIR"
echo ""
echo "OPTION 1: Run from the bot directory:"
echo "  cd '$TARGET_DIR'"
echo "  ./install.sh"
echo "  ./run_bot.sh"
echo ""
echo "OPTION 2: Run from anywhere using the launcher:"
echo "  ~/run_smm_bot.sh"
echo ""
echo "⚠️  Before running the bot, make sure to edit the .env file:"
echo "  nano '$TARGET_DIR/.env'"
echo ""
echo "Need multiple admins? Use comma-separated IDs in the .env file:"
echo "  ADMIN_USER_ID=123456789,987654321,555555555"
echo "---------------------------------------------" 