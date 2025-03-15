from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from utils.db import db
from utils.messages import get_message

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help information and contact details."""
    user_id = update.effective_user.id
    language = db.get_language(user_id)
    
    # Get help text from messages
    help_text = (
        f"{get_message(language, 'help', 'title')}\n\n"
        f"<b>Available commands:</b>\n"
        f"/start - Start the bot\n"
        f"/services - Browse available services\n"
        f"/order - Place a new order\n"
        f"/balance - Check your balance\n"
        f"/status - Check order status\n"
        f"/referrals - View your referrals\n"
        f"/support - Contact customer support\n"
        f"/tutorial - View interactive tutorials\n"
        f"/help - Show this help message\n\n"
        f"{get_message(language, 'help', 'description')}\n"
        f"If you need assistance, you can contact our support team directly through the bot."
    )
    
    # Create keyboard with support button
    keyboard = [
        [InlineKeyboardButton("📚 View Tutorials", callback_data="tutorial")],
        [InlineKeyboardButton(get_message(language, 'help', 'contact_support'), callback_data="start_support_chat")],
        [InlineKeyboardButton(get_message(language, 'help', 'back_to_menu'), callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both callback queries and direct messages
    if update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        update.message.reply_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        
    return