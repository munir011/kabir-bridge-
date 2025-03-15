from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
import logging
from utils.db import db
from utils.helpers import is_admin
from utils.messages import get_message

# Module logger
logger = logging.getLogger(__name__)

def show_command_menu(update: Update, context: CallbackContext) -> None:
    """Show a persistent keyboard with common commands"""
    user = update.effective_user
    
    # Get user's language preference
    language = db.get_language(user.id)
    
    # Check if user is admin
    is_user_admin = is_admin(user.id)
    
    # Get localized command names with translations
    # We keep the /command format for functionality but show translated text
    start_cmd = f"{get_message(language, 'main_menu', 'start', default='Start')} - /start"
    services_cmd = f"{get_message(language, 'main_menu', 'services', default='Services')} - /services"
    recharge_cmd = f"{get_message(language, 'main_menu', 'recharge', default='Recharge')} - /recharge"
    balance_cmd = f"{get_message(language, 'main_menu', 'balance', default='Balance')} - /balance"
    my_orders_cmd = f"{get_message(language, 'main_menu', 'my_orders', default='My Orders')} - /my_orders"
    check_order_cmd = f"{get_message(language, 'main_menu', 'order_status', default='Check Order')} - /check_order"
    referrals_cmd = f"{get_message(language, 'main_menu', 'referrals', default='Referrals')} - /referrals"
    more_cmd = f"{get_message(language, 'main_menu', 'more', default='More')} - /more"
    customer_service_cmd = f"{get_message(language, 'main_menu', 'support', default='Support')} - /customer_service"
    admin_cmd = f"{get_message(language, 'main_menu', 'admin', default='Admin')} - /admin"
    
    # Create a keyboard with command buttons in a grid layout (2 per row)
    keyboard = [
        [KeyboardButton(start_cmd), KeyboardButton(services_cmd)],
        [KeyboardButton(recharge_cmd), KeyboardButton(balance_cmd)],
        [KeyboardButton(my_orders_cmd), KeyboardButton(check_order_cmd)],
        [KeyboardButton(referrals_cmd), KeyboardButton(more_cmd)],
        [KeyboardButton(customer_service_cmd)]
    ]
    
    # Add admin commands if user is admin
    if is_user_admin:
        # Add admin to the last row if it has only one button
        if len(keyboard[-1]) == 1:
            keyboard[-1].append(KeyboardButton(admin_cmd))
        else:
            keyboard.append([KeyboardButton(admin_cmd)])
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False  # Make it persistent
    )
    
    # Apply the keyboard without a visible message
    try:
        # Use a single space character as the message to make it less visible
        # Telegram doesn't allow completely empty messages, so we use a space
        update.message.reply_text(
            " ",
            reply_markup=reply_markup
        )
        context.user_data['command_menu_active'] = True
    except Exception as e:
        logger.error(f"Error showing command menu: {e}")
    
    logger.info(f"Showing command menu for user {user.id}")

def hide_command_menu(update: Update, context: CallbackContext) -> None:
    """Hide the persistent keyboard"""
    try:
        update.message.reply_text(
            " ",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data['command_menu_active'] = False
        logger.info(f"Hiding command menu for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error hiding command menu: {e}")

def toggle_command_menu(update: Update, context: CallbackContext) -> None:
    """Toggle the command menu on/off"""
    user_id = update.effective_user.id
    
    # Check if the user has the menu active (stored in user_data)
    menu_active = context.user_data.get('command_menu_active', False)
    
    if menu_active:
        # Hide the menu
        hide_command_menu(update, context)
    else:
        # Show the menu
        show_command_menu(update, context)

def get_command_menu_handlers():
    """Return the handlers for the command menu"""
    return [
        CommandHandler('menu', toggle_command_menu),
        CommandHandler('showmenu', show_command_menu),
        CommandHandler('hidemenu', hide_command_menu)
    ] 