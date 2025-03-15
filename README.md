# Kabir Bridge Telegram Bot

A powerful Telegram bot for providing quick and efficient online services.

## Overview

Kabir Bridge is a feature-rich Telegram bot that serves as a gateway to various online services. It provides a user-friendly interface with multilingual support, making it accessible to users worldwide.

## Features

- **Multilingual Support**: Available in English, Amharic, Arabic, Hindi, Spanish, Chinese, and Turkish
- **Command Menu**: Easy-to-use persistent keyboard with common commands
- **Service Catalog**: Browse and order from a wide range of online services
- **Order Management**: Place orders and track their status
- **Account Management**: Check balance and recharge your account
- **Referral System**: Invite friends and earn rewards
- **Admin Panel**: Comprehensive tools for administrators

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables in the `.env` file:
   ```
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_USER_ID=your_telegram_user_id
   ```

## Running the Bot

```bash
cd bot
source ../venv_py311/bin/activate
python bot.py
```

Alternatively, you can use the provided shell script:
```bash
./start_bot.sh
```

## Project Structure

- `bot/`: Main bot code
  - `bot.py`: Entry point for the bot
  - `handlers/`: Command handlers and callback functions
  - `utils/`: Utility functions and helpers
  - `data/`: Data storage

## Commands

- `/start` - Start the bot and see the welcome message
- `/services` - Browse available services
- `/order` - Place a new order
- `/status` - Check order status
- `/balance` - Check your balance
- `/recharge` - Add funds to your account
- `/help` - Get help and support
- `/menu` - Show/hide the command menu
- `/my_orders` - View your orders
- `/check_order` - Check a specific order
- `/referrals` - Access the referral program
- `/more` - See additional options
- `/customer_service` - Contact support

## Support

For support, contact:
- Phone: +251907806267
- Telegram: @muay011

## License

This project is proprietary software. All rights reserved.

---

© 2025 Kabir Bridge. All rights reserved. 