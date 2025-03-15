# Telegram SMM Panel Bot

A Telegram bot for managing social media marketing services.

## Setup and Running

1. Make sure you have Python 3.7+ installed on your system.

2. Clone or download this repository to your local machine.

3. Configure the bot by editing the `.env` file in the root directory:
   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_bot_token

   # SMM API Configuration
   API_URL=your_api_url
   API_KEY=your_api_key

   # Admin Configuration
   ADMIN_USER_ID=your_telegram_user_id
   ADMIN_USERNAME=your_telegram_username

   # Database Configuration
   DB_FILE=data/smm_bot.db
   ```

4. Run the bot:
   ```bash
   ./run_clean_bot.sh
   ```

   This script will:
   - Create a Python virtual environment (if it doesn't exist)
   - Install the required dependencies
   - Run the bot

## Features

- Browse and order SMM services
- Check order status
- Manage balance and recharge
- Referral system
- Multi-language support
- Tutorial system for users
- Admin panel for managing the bot

## File Structure

- `bot/` - Contains the main bot code
  - `bot.py` - Main entry point
  - `handlers/` - Command handlers for different features
  - `utils/` - Utility functions
- `data/` - Contains the database file
- `run_clean_bot.sh` - Script to run the bot

## Requirements

- python-telegram-bot==13.15
- python-dotenv==1.0.0
- requests==2.31.0 