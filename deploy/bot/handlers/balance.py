import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from utils.db import db
from utils.constants import CURRENCY_RATES
from utils.messages import get_message

logger = logging.getLogger(__name__)

def balance_command(update: Update, context: CallbackContext):
    """Handler for /balance command"""
    user = update.effective_user
    logger.info(f"Balance command called by user {user.id}")
    
    # Update user activity and ensure user exists in database
    db.update_user_activity(user.id)
    
    try:
        # Get user's balance from local database
        balance = db.get_balance(user.id)
        logger.info(f"User {user.id} balance: {balance}")
        
        # Get user's currency preference
        currency_preference = db.get_currency_preference(user.id)
        logger.info(f"User {user.id} currency preference: {currency_preference}")
        
        # Get user's language preference
        language = db.get_language(user.id)
        logger.info(f"User {user.id} language preference: {language}")
        
        # Get recent transactions
        transactions = db.get_transactions(user.id, limit=5)
        logger.info(f"User {user.id} has {len(transactions)} recent transactions")
        
        # Create balance info message using language-specific messages
        title = get_message(language, 'balance', 'title')
        logger.info(f"Balance title for language {language}: {title}")
        message = f"{title}\n\n"
        
        # Display balance based on currency preference
        if currency_preference == 'ETB':
            # Convert USD balance to ETB
            etb_balance = balance * CURRENCY_RATES["ETB"]
            formatted_etb = f"{etb_balance:,.0f}"
            balance_text = get_message(language, 'balance', 'current_balance_etb')
            logger.info(f"ETB balance text for language {language}: {balance_text}")
            message += balance_text.format(
                formatted_etb=formatted_etb, 
                balance=balance
            ) + "\n\n"
        else:
            balance_text = get_message(language, 'balance', 'current_balance_usd')
            logger.info(f"USD balance text for language {language}: {balance_text}")
            message += balance_text.format(
                balance=balance
            ) + "\n\n"
        
        # Add recent transactions section if there are any
        if transactions:
            transactions_title = get_message(language, 'balance', 'recent_transactions')
            logger.info(f"Transactions title for language {language}: {transactions_title}")
            message += transactions_title + "\n\n"
            for tx in transactions:
                amount = tx['amount']
                symbol = "+" if tx['type'] == 'credit' else "-"
                
                # Format transaction amount based on currency preference
                if currency_preference == 'ETB':
                    etb_amount = abs(amount) * CURRENCY_RATES["ETB"]
                    formatted_etb = f"{etb_amount:,.0f}"
                    message += (
                        f"{'💵' if tx['type'] == 'credit' else '🔄'} "
                        f"{symbol}ETB {formatted_etb} (≈${abs(amount):.2f}) - {tx['description']}\n"
                        f"📅 {tx['created_at'][:10]}\n\n"
                    )
                else:
                    message += (
                        f"{'💵' if tx['type'] == 'credit' else '🔄'} "
                        f"{symbol}${abs(amount):.2f} - {tx['description']}\n"
                        f"📅 {tx['created_at'][:10]}\n\n"
                    )
        else:
            no_transactions_text = get_message(language, 'balance', 'no_transactions')
            logger.info(f"No transactions text for language {language}: {no_transactions_text}")
            message += no_transactions_text + "\n"
        
        # Add note about adding balance
        add_balance_note = get_message(language, 'balance', 'add_balance_note')
        logger.info(f"Add balance note for language {language}: {add_balance_note}")
        message += "\n" + add_balance_note
        
        # Create refresh button and add fund button
        refresh_button_text = get_message(language, 'balance', 'refresh_button')
        logger.info(f"Refresh button text for language {language}: {refresh_button_text}")
        
        # Get add fund button text - use recharge text if available, otherwise default to "Add Fund"
        add_fund_text = get_message(language, 'main_menu', 'recharge') if get_message(language, 'main_menu', 'recharge') else "💰 Add Fund"
        
        keyboard = [
            [
                InlineKeyboardButton(refresh_button_text, callback_data="refresh_balance"),
                InlineKeyboardButton(add_fund_text, callback_data="recharge")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Log the final message
        logger.info(f"Final balance message for user {user.id}: {message}")
        
        # Send or edit message based on update type
        if update.callback_query:
            update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            update.message.reply_html(
                message,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error in balance command: {e}", exc_info=True)
        language = db.get_language(user.id)
        error_message = get_message(language, 'balance', 'error_message')
        
        if update.callback_query:
            update.callback_query.edit_message_text(error_message)
        else:
            update.message.reply_text(error_message)

def refresh_balance_callback(update: Update, context: CallbackContext):
    """Handle refresh balance button"""
    query = update.callback_query
    user = update.effective_user
    language = db.get_language(user.id)
    
    query.answer(get_message(language, 'balance', 'refreshed'))
    
    try:
        # Get user's balance from local database
        balance = db.get_balance(user.id)
        
        # Get user's currency preference
        currency_preference = db.get_currency_preference(user.id)
        
        # Get recent transactions
        transactions = db.get_transactions(user.id, limit=5)
        
        # Create balance info message using language-specific messages
        message = f"{get_message(language, 'balance', 'title')}\n\n"
        
        # Display balance based on currency preference
        if currency_preference == 'ETB':
            # Convert USD balance to ETB
            etb_balance = balance * CURRENCY_RATES["ETB"]
            formatted_etb = f"{etb_balance:,.0f}"
            message += get_message(language, 'balance', 'current_balance_etb').format(
                formatted_etb=formatted_etb, 
                balance=balance
            ) + "\n\n"
        else:
            message += get_message(language, 'balance', 'current_balance_usd').format(
                balance=balance
            ) + "\n\n"
        
        # Add recent transactions section if there are any
        if transactions:
            message += get_message(language, 'balance', 'recent_transactions') + "\n\n"
            for tx in transactions:
                amount = tx['amount']
                symbol = "+" if tx['type'] == 'credit' else "-"
                
                # Format transaction amount based on currency preference
                if currency_preference == 'ETB':
                    etb_amount = abs(amount) * CURRENCY_RATES["ETB"]
                    formatted_etb = f"{etb_amount:,.0f}"
                    message += (
                        f"{'💵' if tx['type'] == 'credit' else '🔄'} "
                        f"{symbol}ETB {formatted_etb} (≈${abs(amount):.2f}) - {tx['description']}\n"
                        f"📅 {tx['created_at'][:10]}\n\n"
                    )
                else:
                    message += (
                        f"{'💵' if tx['type'] == 'credit' else '🔄'} "
                        f"{symbol}${abs(amount):.2f} - {tx['description']}\n"
                        f"📅 {tx['created_at'][:10]}\n\n"
                    )
        else:
            message += get_message(language, 'balance', 'no_transactions') + "\n"
        
        # Add note about adding balance
        message += "\n" + get_message(language, 'balance', 'add_balance_note')
        
        # Create refresh button and add fund button
        keyboard = [
            [
                InlineKeyboardButton(get_message(language, 'balance', 'refresh_button'), callback_data="refresh_balance"),
                InlineKeyboardButton(get_message(language, 'main_menu', 'recharge'), callback_data="recharge")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Update the message
        try:
            query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            # If the message is the same, just answer the callback query
            query.answer(get_message(language, 'balance', 'up_to_date'))
    except Exception as e:
        logger.error(f"Error in refresh_balance_callback: {e}")
        query.edit_message_text(
            get_message(language, 'balance', 'error_refresh')
        )
    
    return 