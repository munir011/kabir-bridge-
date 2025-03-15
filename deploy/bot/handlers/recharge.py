import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from utils.db import db
from utils.helpers import is_admin
from utils.constants import CURRENCY_RATES
from utils.messages import get_message

logger = logging.getLogger(__name__)

# States
AMOUNT = 1
RECEIPT = 2

# Admin contact and ID
ADMIN_USERNAME = "@muay011"
# Get the first admin ID for direct messaging
admin_ids_str = os.getenv("ADMIN_USER_ID", "0")
ADMIN_ID = int(admin_ids_str.split(",")[0]) if admin_ids_str else 0

# Wise Contact Information
WISE_CONTACT_INFO = ""

# Currency exchange rates (USD to other currencies)
CURRENCY_RATES = {
    "ETB": 155.5,  # 1 USD = 56.5 ETB (Ethiopian Birr)
    "EUR": 0.925,  # 1 USD = 0.92 EUR
    "GBP": 0.80,  # 1 USD = 0.78 GBP
    "AUD": 1.75,  # 1 USD = 1.52 AUD
    "AED": 3.695,  # 1 USD = 3.67 AED
    "CAD": 1.46,  # 1 USD = 1.37 CAD
}

# Payment details
PAYMENT_METHODS = {
    "cbe": {
        "bank": "🏦 CBE (Commercial Bank of Ethiopia)",
        "account": "1000388630209",
        "name": "Munir Ayub Mohammed"
    },
    "awash": {
        "bank": "🏦 Awash Bank",
        "account": "01425722099900",
        "name": "Munir Ayub Mohammed"
    },
    "abyssinia": {
        "bank": "🏦 Bank of Abyssinia",
        "account": "98216006",
        "name": "Munir Ayub"
    },
    "dashen": {
        "bank": "🏦 Dashen Bank",
        "account": "2944341676911",
        "name": "Munir Ayub Mohammed"
    },
    "coop": {
        "bank": "🏦 Cooperative Bank",
        "account": "1004600085588",
        "name": "Munir Ayub Mohammed"
    },
    "ebirr": {
        "bank": "📱 E-Birr",
        "account": "0907806267",
        "name": "Munir Ayub Mohammed"
    },
    "telebirr": {
        "bank": "📱 Telebirr",
        "account": "0907806267",
        "name": "Munir Ayub Mohammed"
    }
}

# International payment details
INTERNATIONAL_PAYMENT_METHODS = {
    "wise": {
        "method": "🌐 Wise",
        "currencies": {
            "usd": {
                "flag": "🇺🇸",
                "name": "USD",
                "details": """Name: Munir ayub Mohammed
Account number: 446994570792362
Account type: Deposit
Routing number (for wire and ACH): 084009519
Swift/BIC: TRWIUS35XXX
Address: Wise US Inc, 30 W. 26th Street, Sixth Floor, New York, NY, 10010, United States"""
            },
            "eur": {
                "flag": "🇪🇺",
                "name": "EUR",
                "details": """Name: Munir ayub Mohammed
IBAN: BE84 9052 0161 0059
Swift/BIC: TRWIBEB1XXX
Bank name and address: Wise, Rue du Trône 100, 3rd floor, Brussels, 1050, Belgium"""
            },
            "gbp": {
                "flag": "🇬🇧",
                "name": "GBP",
                "details": """Name: Munir ayub Mohammed
Account number: 16418985
Sort code: 23-08-01
IBAN: GB53 TRWI 2308 0116 4189 85
Swift/BIC: TRWIGB2LXXX
Bank name and address: Wise Payments Limited, 56 Shoreditch High Street, London, E1 6JJ, United Kingdom"""
            },
            "aud": {
                "flag": "🇦🇺",
                "name": "AUD",
                "details": """Name: Munir ayub Mohammed
Account number: 226530851
BSB code: 774001
Swift/BIC: TRWIAUS1XXX
Bank name and address: Wise Australia Pty Ltd, Suite 1, Level 11, 66 Goulburn Street, Sydney, NSW, 2000, Australia"""
            },
            "aed": {
                "flag": "🇦🇪",
                "name": "AED",
                "details": """Name: Munir ayub Mohammed
IBAN: GB53 TRWI 2308 0116 4189 85
Swift/BIC: TRWIGB2LXXX
Bank name and address: Wise Payments Limited, 56 Shoreditch High Street, London, E1 6JJ, United Kingdom"""
            },
            "cad": {
                "flag": "🇨🇦",
                "name": "CAD",
                "details": """Name: Munir ayub Mohammed
Account number: 200116751521
Institution number: 621
Transit number: 16001
Swift/BIC: TRWICAW1XXX
Bank name and address: Wise Payments Canada Inc., 99 Bank Street, Suite 1420, Ottawa, ON, K1P 1H4, Canada"""
            }
        },
        "name": "Munir Ayub Mohammed",
        "email": "munirayub011@gmail.com",
        "phone": "+251907806267",
        "payment_link": "https://wise.com/pay/me/munirauubm"
    },
    "dukascopy": {
        "method": "🏦 Dukascopy Bank",
        "details": """Account: 1472225
Email: munirayub011@gmail.com
Phone: +251 90 780 6267""",
        "name": "Munir Ayub Mohammed"
    }
}

# Cryptocurrency payment details
CRYPTO_PAYMENT_METHODS = {
    "binance": {
        "method": "💰 Binance ID",
        "uid": "392268780",
        "name": "Munir Ayub Mohammed"
    },
    "okx": {
        "method": "💰 OKX UID",
        "uid": "581498229339357572",
        "name": "Munir Ayub Mohammed"
    },
    "bybit": {
        "method": "💰 Bybit UID",
        "uid": "31725087",
        "name": "Munir Ayub Mohammed"
    },
    "mexc": {
        "method": "💰 Mexc UID",
        "uid": "37870637",
        "name": "Munir Ayub Mohammed"
    }
}

def recharge_command(update: Update, context: CallbackContext):
    """Handler for /recharge command"""
    user = update.effective_user
    db.update_user_activity(user.id)
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    message = (
        f"{get_message(language, 'recharge', 'title')}\n\n"
        f"{get_message(language, 'recharge', 'select_payment_method')}"
    )
    
    # Create keyboard with payment method options
    keyboard = [
        [InlineKeyboardButton(get_message(language, 'recharge', 'wise'), callback_data="method_wise")],
        [InlineKeyboardButton("🇪🇹 " + get_message(language, 'recharge', 'eth_banks'), callback_data="method_eth")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'intl_options'), callback_data="method_intl")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'crypto'), callback_data="method_crypto")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'cancel'), callback_data="method_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or direct command
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        # This is a direct command
        update.message.reply_html(message, reply_markup=reply_markup)
    
    return ConversationHandler.END

def handle_method_selection(update: Update, context: CallbackContext):
    """Handle payment method selection"""
    query = update.callback_query
    user = update.effective_user
    data = query.data.split('_')[1]
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    if data == "cancel":
        query.edit_message_text(
            get_message(language, 'recharge', 'cancelled')
        )
        return ConversationHandler.END
    
    # Store selected payment method in context
    context.user_data['selected_method'] = data
    
    # Show amount options based on payment method
    if data == "eth":
        # For Ethiopian banks, show amounts in ETB
        show_eth_amount_options(update, context)
    else:
        # For other methods, show amounts in USD
        show_usd_amount_options(update, context)
    
    return ConversationHandler.END

def show_eth_amount_options(update: Update, context: CallbackContext):
    """Show amount options in ETB for Ethiopian banks"""
    query = update.callback_query
    
    # Use ETB-specific amounts
    etb_amounts = [100, 500, 1000, 5000, 10000, 50000, 100000]
    
    # Calculate approximate USD equivalents
    usd_equivalents = [round(etb / CURRENCY_RATES["ETB"], 2) for etb in etb_amounts]
    
    message = (
        "💳 <b>Recharge Account - 🇪🇹 Ethiopian Banks</b>\n\n"
        "Please select the amount you want to recharge:\n\n"
        "Choose from preset amounts or click 'Custom Amount' to enter your own."
    )
    
    # Create keyboard with preset amounts in ETB and custom amount option
    keyboard = [
        [
            InlineKeyboardButton(f"ETB {etb_amounts[0]} (≈${usd_equivalents[0]})", callback_data=f"recharge_eth_{usd_equivalents[0]}"),
            InlineKeyboardButton(f"ETB {etb_amounts[1]} (≈${usd_equivalents[1]})", callback_data=f"recharge_eth_{usd_equivalents[1]}")
        ],
        [
            InlineKeyboardButton(f"ETB {etb_amounts[2]} (≈${usd_equivalents[2]})", callback_data=f"recharge_eth_{usd_equivalents[2]}"),
            InlineKeyboardButton(f"ETB {etb_amounts[3]} (≈${usd_equivalents[3]})", callback_data=f"recharge_eth_{usd_equivalents[3]}")
        ],
        [
            InlineKeyboardButton(f"ETB {etb_amounts[4]} (≈${usd_equivalents[4]})", callback_data=f"recharge_eth_{usd_equivalents[4]}"),
            InlineKeyboardButton(f"ETB {etb_amounts[5]} (≈${usd_equivalents[5]})", callback_data=f"recharge_eth_{usd_equivalents[5]}")
        ],
        [
            InlineKeyboardButton(f"ETB {etb_amounts[6]} (≈${usd_equivalents[6]})", callback_data=f"recharge_eth_{usd_equivalents[6]}")
        ],
        [InlineKeyboardButton("💰 Custom Amount", callback_data="recharge_eth_custom")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_methods")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

def show_usd_amount_options(update: Update, context: CallbackContext):
    """Show amount options in USD for international payments"""
    query = update.callback_query
    user = update.effective_user
    method = context.user_data.get('selected_method', 'intl')
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    method_titles = {
        "wise": "Wise (International)",
        "intl": "International Options",
        "crypto": "Cryptocurrency"
    }
    
    title = method_titles.get(method, "Recharge")
    
    message = (
        f"{get_message(language, 'recharge', 'title')} - {title}\n\n"
        f"{get_message(language, 'recharge', 'select_amount')}"
    )
    
    # Create keyboard with preset amounts in USD and custom amount option
    keyboard = [
        [
            InlineKeyboardButton("$10", callback_data=f"recharge_{method}_10"),
            InlineKeyboardButton("$25", callback_data=f"recharge_{method}_25"),
            InlineKeyboardButton("$50", callback_data=f"recharge_{method}_50")
        ],
        [
            InlineKeyboardButton("$100", callback_data=f"recharge_{method}_100"),
            InlineKeyboardButton("$500", callback_data=f"recharge_{method}_500"),
            InlineKeyboardButton("$1000", callback_data=f"recharge_{method}_1000")
        ],
        [
            InlineKeyboardButton("$5000", callback_data=f"recharge_{method}_5000"),
            InlineKeyboardButton("$10000", callback_data=f"recharge_{method}_10000")
        ],
        [InlineKeyboardButton(get_message(language, 'recharge', 'custom_amount'), callback_data=f"recharge_{method}_custom")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'back'), callback_data="back_to_methods")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

def handle_back_to_methods(update: Update, context: CallbackContext):
    """Handle back button to return to payment methods"""
    query = update.callback_query
    user = update.effective_user
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    message = (
        f"{get_message(language, 'recharge', 'title')}\n\n"
        f"{get_message(language, 'recharge', 'select_payment_method')}"
    )
    
    # Create keyboard with payment method options
    keyboard = [
        [InlineKeyboardButton(get_message(language, 'recharge', 'wise'), callback_data="method_wise")],
        [InlineKeyboardButton("🇪🇹 " + get_message(language, 'recharge', 'eth_banks'), callback_data="method_eth")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'intl_options'), callback_data="method_intl")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'crypto'), callback_data="method_crypto")],
        [InlineKeyboardButton(get_message(language, 'recharge', 'cancel'), callback_data="method_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

def handle_recharge_callback(update: Update, context: CallbackContext):
    """Handle recharge amount selection"""
    query = update.callback_query
    user = update.effective_user
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    # Extract method and amount from callback data
    data = query.data.split('_')
    
    # Check if we have enough elements in the data list
    if len(data) < 3:
        # Handle the case where there's no amount_type (like "recharge_account")
        if data[0] == "recharge" and data[1] == "account":
            # Redirect to the recharge command
            return recharge_command(update, context)
        else:
            # Log the unexpected callback data
            logger.warning(f"Unexpected callback data format: {query.data}")
            query.answer("Invalid selection. Please try again.")
            return ConversationHandler.END
    
    # If we have enough elements, proceed as before
    method = data[1]
    amount_type = data[2]
    
    if amount_type == "custom":
        # Handle custom amount entry
        if method == "eth":
            query.edit_message_text(
                get_message(language, 'recharge', 'custom_amount_etb'),
                parse_mode="HTML"
            )
            context.user_data['custom_amount_type'] = 'eth'
        else:
            query.edit_message_text(
                get_message(language, 'recharge', 'custom_amount_usd'),
                parse_mode="HTML"
            )
            context.user_data['custom_amount_type'] = 'usd'
        return AMOUNT
    
    # Handle preset amount
    amount = float(amount_type)
    
    # Process the amount based on the selected method
    if method == "wise":
        handle_wise_direct(update, context, amount)
    elif method == "eth":
        show_bank_options(update, context, amount)
    elif method == "intl":
        show_international_options(update, context, amount)
    elif method == "crypto":
        show_crypto_options(update, context, amount)
    else:
        # Fallback to payment methods selection
        show_payment_methods(update, context, amount)
    
    return ConversationHandler.END

def handle_custom_amount(update: Update, context: CallbackContext):
    """Handle custom recharge amount"""
    user = update.effective_user
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    try:
        amount_type = context.user_data.get('custom_amount_type', 'usd')
        method = context.user_data.get('selected_method', 'intl')
        
        amount = float(update.message.text.strip())
        
        # Validate amount based on currency and payment method
        if amount_type == 'eth':
            # For ETB, minimum amount is 100
            if amount < 100:
                update.message.reply_html(
                    get_message(language, 'recharge', 'minimum_amount_etb')
                )
                return AMOUNT
        else:
            # For USD and international methods (Wise, crypto), enforce a $10 minimum
            if method in ["wise", "intl", "crypto"] and amount < 10:
                update.message.reply_html(
                    f"⚠️ The minimum amount for international payments is <b>$10</b>. Please enter a larger amount."
                )
                return AMOUNT
            # For other USD methods, minimum amount is 1
            elif amount < 1:
                update.message.reply_html(
                    get_message(language, 'recharge', 'minimum_amount_usd')
                )
                return AMOUNT
        
        if amount_type == 'eth':
            # Convert ETB to USD for internal processing
            usd_amount = amount / CURRENCY_RATES["ETB"]
            show_bank_options(update, context, usd_amount, original_etb=amount)
        else:
            # Handle USD amount based on selected method
            if method == "wise":
                # For text message input, use reply_html instead of edit_message_text
                handle_wise_direct_message(update, context, amount)
            elif method == "intl":
                # For text message input, use reply_html instead of edit_message_text
                show_international_options_message(update, context, amount)
            elif method == "crypto":
                # For text message input, use reply_html instead of edit_message_text
                show_crypto_options_message(update, context, amount)
            else:
                # Fallback to payment methods selection
                show_payment_methods(update, context, amount)
        
        return ConversationHandler.END
        
    except ValueError:
        currency = "ETB" if context.user_data.get('custom_amount_type') == 'eth' else "$"
        update.message.reply_html(
            get_message(language, 'recharge', 'invalid_amount').format(currency=currency)
        )
        return AMOUNT

def show_bank_options(update: Update, context: CallbackContext, amount: float, original_etb=None):
    """Show available bank options"""
    # Calculate ETB amount if not provided
    etb_amount = original_etb if original_etb is not None else amount * CURRENCY_RATES["ETB"]
    
    # Format ETB amount with commas for better readability
    formatted_etb = f"{etb_amount:,.0f}"
    
    message = (
        f"🏦 <b>Select 🇪🇹 Ethiopian Bank</b>\n\n"
        f"<b>Amount to pay:</b> <code>ETB {formatted_etb}</code> (≈${amount:.2f})\n\n"
        f"Please choose your preferred bank:"
    )
    
    # Create keyboard with bank options
    keyboard = [
        [InlineKeyboardButton("🏦 CBE (Commercial Bank of Ethiopia)", callback_data=f"bank_cbe_{amount}")],
        [InlineKeyboardButton("🏦 Awash Bank", callback_data=f"bank_awash_{amount}")],
        [InlineKeyboardButton("🏦 Bank of Abyssinia", callback_data=f"bank_abyssinia_{amount}")],
        [InlineKeyboardButton("🏦 Dashen Bank", callback_data=f"bank_dashen_{amount}")],
        [InlineKeyboardButton("🏦 Cooperative Bank", callback_data=f"bank_coop_{amount}")],
        [InlineKeyboardButton("📱 E-Birr", callback_data=f"bank_ebirr_{amount}")],
        [InlineKeyboardButton("📱 Telebirr", callback_data=f"bank_telebirr_{amount}")],
        [InlineKeyboardButton("🔙 Back", callback_data="method_eth")],
        [InlineKeyboardButton("❌ Cancel", callback_data="method_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        update.message.reply_html(message, reply_markup=reply_markup)

def show_payment_methods(update: Update, context: CallbackContext, amount: float):
    """Show available payment methods"""
    message = (
        f"💳 <b>Select Payment Method</b>\n\n"
        f"Amount to recharge: <code>${amount:.2f}</code>\n\n"
        f"Please choose your preferred payment method:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🌐 Wise (International)", callback_data=f"intl_wise_direct_{amount}")],
        [InlineKeyboardButton("🏦 Ethiopian Banks", callback_data=f"pay_eth_{amount}")],
        [InlineKeyboardButton("🌍 Other International Options", callback_data=f"pay_intl_{amount}")],
        [InlineKeyboardButton("₿ Cryptocurrency", callback_data=f"pay_crypto_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        update.message.reply_html(message, reply_markup=reply_markup)

def show_international_options(update: Update, context: CallbackContext, amount: float):
    """Show available international payment options"""
    message = (
        f"🌍 <b>International Payment Options</b>\n\n"
        f"Amount to pay: <code>${amount:.2f}</code>\n\n"
        f"Please choose your preferred payment method:"
    )
    
    # Create keyboard with international payment options
    keyboard = [
        [InlineKeyboardButton("🌐 Wise (Recommended)", callback_data=f"intl_wise_direct_{amount}")],
        [InlineKeyboardButton("🇺🇸 USD", callback_data=f"intl_usd_{amount}")],
        [InlineKeyboardButton("🇪🇺 EUR", callback_data=f"intl_eur_{amount}")],
        [InlineKeyboardButton("🇬🇧 GBP", callback_data=f"intl_gbp_{amount}")],
        [InlineKeyboardButton("🇦🇺 AUD", callback_data=f"intl_aud_{amount}")],
        [InlineKeyboardButton("🇦🇪 AED", callback_data=f"intl_aed_{amount}")],
        [InlineKeyboardButton("🇨🇦 CAD", callback_data=f"intl_cad_{amount}")],
        [InlineKeyboardButton("🏦 Dukascopy Bank", callback_data=f"intl_dukascopy_{amount}")],
        [InlineKeyboardButton("💬 Contact Admin Directly", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pay_back_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or direct message
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

def show_crypto_options(update: Update, context: CallbackContext, amount: float):
    """Show available cryptocurrency payment options"""
    message = (
        f"₿ <b>Cryptocurrency Payment Options</b>\n\n"
        f"Amount to pay: <code>${amount:.2f}</code>\n\n"
        f"Please choose your preferred option:"
    )
    
    # Create simplified crypto options
    keyboard = [
        [InlineKeyboardButton("💰 Binance ID", callback_data=f"crypto_binance_{amount}")],
        [InlineKeyboardButton("💰 OKX UID", callback_data=f"crypto_okx_{amount}")],
        [InlineKeyboardButton("💰 Bybit UID", callback_data=f"crypto_bybit_{amount}")],
        [InlineKeyboardButton("💰 Mexc UID", callback_data=f"crypto_mexc_{amount}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pay_back_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or direct message
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

def handle_payment_method(update: Update, context: CallbackContext):
    """Handle payment method selection"""
    query = update.callback_query
    user = update.effective_user
    data = query.data.split('_')
    
    # Get user's language preference
    language = db.get_language(user.id)
    logger.info(f"User {user.id} language preference: {language}")
    
    if data[1] == "cancel":
        query.edit_message_text(
            get_message(language, 'recharge', 'cancelled')
        )
        return ConversationHandler.END
        
    if data[1] == "back":
        # Go back to payment methods selection
        amount = float(data[2])
        show_payment_methods(update, context, amount)
        return ConversationHandler.END
        
    method = data[1]
    amount = float(data[2])
    
    if method == "eth":
        # Show bank selection options
        show_bank_options(update, context, amount)
        return ConversationHandler.END
    elif method == "intl":
        # Show international payment options
        show_international_options(update, context, amount)
        return ConversationHandler.END
    elif method == "crypto":
        # Show cryptocurrency options
        show_crypto_options(update, context, amount)
        return ConversationHandler.END

def handle_wise_direct(update: Update, context: CallbackContext, amount: float):
    """Handle direct Wise payment"""
    # Store payment info in context for later use
    context.user_data['payment_info'] = {
        'amount': amount,
        'amount_local': amount,
        'currency': 'USD',
        'bank': "Wise Direct Payment",
        'account': "Direct payment via Wise"
    }
    
    # Get Wise payment details
    wise_info = INTERNATIONAL_PAYMENT_METHODS["wise"]
    
    # Format the details in a cleaner way
    formatted_details = (
        "Name: Munir Ayub\n"
        "Email: <code>munirayub011@gmail.com</code>\n"
        "Payment Link: <code>https://wise.com/pay/me/munirauubm</code>"
    )
    
    message = (
        f"🌐 <b>Wise Direct Payment Details</b>\n\n"
        f"<b>Amount to pay:</b> <code>${amount:.2f}</code>\n\n"
        f"<b>Account Details:</b>\n"
        f"{formatted_details}\n\n"
        f"<b>Payment Instructions:</b>\n"
        f"1. Log in to your Wise account or use the payment link\n"
        f"2. Send the exact amount shown above\n"
        f"3. Take a screenshot of the payment confirmation\n\n"
        f"After payment, click 'I've Paid' and send the screenshot when prompted."
    )
    
    # Add "I've Paid" and "Back" buttons
    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_wise_direct_{amount}")],
        [InlineKeyboardButton("🔙 Back to Options", callback_data=f"pay_intl_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or direct message
    if update.callback_query:
        update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_html(message, reply_markup=reply_markup)
    
    return ConversationHandler.END

def handle_crypto_selection(update: Update, context: CallbackContext):
    """Handle cryptocurrency selection"""
    query = update.callback_query
    data = query.data.split('_')
    crypto_code = data[1]
    amount = float(data[2])
    
    # Get crypto details
    crypto_info = CRYPTO_PAYMENT_METHODS.get(crypto_code)
    if not crypto_info:
        query.answer("Invalid exchange option")
        return ConversationHandler.END
    
    # Store payment info in context for later use
    context.user_data['payment_info'] = {
        'amount': amount,
        'amount_local': amount,
        'currency': 'USD',
        'bank': crypto_info['method'],
        'account': crypto_info['uid']
    }
    
    # Show only the selected exchange UID
    message = (
        f"💰 <b>{crypto_info['method']}</b>\n\n"
        f"<b>Amount to pay:</b> <code>${amount:.2f}</code>\n\n"
        f"<b>{crypto_info['method']}:</b> <code>{crypto_info['uid']}</code>\n\n"
        f"After payment, click 'I've Paid' and send the screenshot when prompted."
    )
    
    # Add "I've Paid" and "Back" buttons
    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_crypto_{crypto_code}_{amount}")],
        [InlineKeyboardButton("🔙 Back to Options", callback_data=f"pay_crypto_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

def handle_paid_confirmation(update: Update, context: CallbackContext):
    """Handle 'I've Paid' button click"""
    query = update.callback_query
    data = query.data.split('_')
    
    # Handle different payment formats
    if len(data) == 3:  # Standard format: paid_bankcode_amount
        payment_type = "local"
        bank_code = data[1]
        amount = float(data[2])
    elif len(data) == 4:  # International/Crypto format: paid_intl/crypto_methodcode_amount
        payment_type = data[1]  # "intl" or "crypto"
        bank_code = data[2]  # payment method code
        amount = float(data[3])
    else:
        query.answer("Invalid payment data")
        return ConversationHandler.END
    
    message = (
        "📸 <b>Payment Confirmation</b>\n\n"
        "Please send a photo of your payment receipt or transaction confirmation.\n\n"
        "Make sure the following details are clearly visible:\n"
        "- Transaction Date\n"
        "- Amount\n"
        "- Account/Wallet Address\n"
        "- Transaction ID/Reference"
    )
    
    query.edit_message_text(message, parse_mode="HTML")
    
    # Set state to wait for receipt
    context.user_data['receipt_state'] = {
        'payment_type': payment_type,
        'bank_code': bank_code,
        'amount': amount
    }
    return RECEIPT

def handle_receipt_photo(update: Update, context: CallbackContext):
    """Handle receipt photo submission"""
    user = update.effective_user
    payment_info = context.user_data.get('payment_info', {})
    
    if not update.message.photo:
        update.message.reply_html(
            "❌ Please send a photo of your receipt.\n"
            "The image should clearly show the payment details."
        )
        return RECEIPT
    
    # Get the largest photo size
    photo = update.message.photo[-1]
    
    # Send confirmation message to user
    update.message.reply_html(
        "✅ <b>Receipt Received!</b>\n\n"
        "Your payment is being verified by admin.\n"
        "You will be notified once your balance is updated.\n\n"
        "Use /start to return to the main menu."
    )
    
    # Create verification buttons for admin
    keyboard = [
        [
            InlineKeyboardButton("✅ Verify", callback_data=f"verify_{user.id}_{payment_info.get('amount', 0)}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}_{payment_info.get('amount', 0)}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Prepare amount display with local currency if available
    amount_display = f"<code>${payment_info.get('amount', 'N/A'):.2f}</code>"
    if 'amount_local' in payment_info and 'currency' in payment_info and payment_info['currency'] != 'USD':
        amount_display += f" ({payment_info['currency']} {payment_info['amount_local']:.2f})"
    
    # Forward receipt and details to admin
    admin_message = (
        f"💰 <b>New Payment Submission</b>\n\n"
        f"From User: {user.mention_html()}\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Amount: {amount_display}\n"
        f"Payment Method: {payment_info.get('bank', 'N/A')}\n"
        f"Account: <code>{payment_info.get('account', 'N/A')}</code>\n\n"
        f"Please verify or reject this payment."
    )
    
    # First forward the photo
    context.bot.send_photo(
        chat_id=ADMIN_ID,  # Send to admin
        photo=photo.file_id,
        caption=admin_message,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    
    # Clear payment info from context
    context.user_data.pop('payment_info', None)
    context.user_data.pop('receipt_state', None)
    
    return ConversationHandler.END

def handle_verification(update: Update, context: CallbackContext):
    """Handle admin's verification decision"""
    query = update.callback_query
    
    # Only admin can verify payments
    if not is_admin(query.from_user.id):
        query.answer("You are not authorized to perform this action.")
        return ConversationHandler.END
    
    # Extract data from callback
    data = query.data.split('_')
    action = data[0]  # 'verify' or 'reject'
    user_id = int(data[1])
    amount = float(data[2])
    
    # Get user's currency preference
    currency_preference = db.get_currency_preference(user_id)
    
    if action == "verify":
        # Add balance to user's account
        db.add_balance(user_id, amount, "Payment verification")
        
        # Default to ETB for currency preference if not specified in callback data
        # This is for backward compatibility with existing buttons
        if len(data) > 3 and data[3] == "etb":
            db.update_currency_preference(user_id, "ETB")
            currency_preference = "ETB"
        
        # Notify admin
        query.edit_message_caption(
            caption=f"✅ Payment Verified\n\n"
                   f"User ID: {user_id}\n"
                   f"Amount: ${amount:.2f}"
        )
        
        # Prepare notification based on currency preference
        if currency_preference == 'ETB':
            etb_amount = amount * CURRENCY_RATES["ETB"]
            notification = (
                f"💰 <b>Payment Verified!</b>\n\n"
                f"Your payment of <b>${amount:.2f}</b> (ETB {etb_amount:.2f}) has been verified.\n"
                f"Your balance has been updated.\n\n"
                f"Thank you for using our service!"
            )
        else:
            notification = (
                f"💰 <b>Payment Verified!</b>\n\n"
                f"Your payment of <b>${amount:.2f}</b> has been verified.\n"
                f"Your balance has been updated.\n\n"
                f"Thank you for using our service!"
            )
        
        # Notify user
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=notification,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about payment verification: {e}")
    
    elif action == "reject":
        # Notify admin
        query.edit_message_caption(
            caption=f"❌ Payment Rejected\n\n"
                   f"User ID: {user_id}\n"
                   f"Amount: ${amount:.2f}"
        )
        
        # Notify user
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ <b>Payment Rejected</b>\n\n"
                    f"Your payment of <b>${amount:.2f}</b> could not be verified.\n"
                    f"Please contact support for assistance."
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about payment rejection: {e}")
    
    return ConversationHandler.END

def handle_bank_selection(update: Update, context: CallbackContext):
    """Handle bank selection"""
    query = update.callback_query
    data = query.data.split('_')
    bank_code = data[1]
    amount = float(data[2])
    
    # Calculate ETB amount
    etb_amount = amount * CURRENCY_RATES["ETB"]
    
    # Format ETB amount with commas for better readability
    formatted_etb = f"{etb_amount:,.0f}"
    
    bank_info = PAYMENT_METHODS[bank_code]
    
    # Store payment info in context for later use
    context.user_data['payment_info'] = {
        'amount': amount,
        'amount_local': etb_amount,
        'currency': 'ETB',
        'bank': bank_info['bank'],
        'account': bank_info['account'],
        'is_ethiopian_bank': True  # Flag to identify Ethiopian bank payments
    }
    
    message = (
        f"🏦 <b>{bank_info['bank']} Payment Details</b>\n\n"
        f"<b>Amount to pay:</b> <code>ETB {formatted_etb}</code> (≈${amount:.2f})\n\n"
        f"<b>Account Details:</b>\n"
        f"Account Number: <code>{bank_info['account']}</code>\n"
        f"Account Name: {bank_info['name']}\n\n"
        f"<b>Payment Instructions:</b>\n"
        f"1. Log in to your bank account or mobile banking app\n"
        f"2. Make a transfer of <b>ETB {formatted_etb}</b> using the details above\n"
        f"3. Take a screenshot of the payment confirmation\n\n"
        f"After payment, click 'I've Paid' and send the screenshot when prompted."
    )
    
    # Add "I've Paid" and "Back" buttons
    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_{bank_code}_{amount}")],
        [InlineKeyboardButton("🔙 Back to Banks", callback_data="method_eth")],
        [InlineKeyboardButton("❌ Cancel", callback_data="method_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

def handle_international_selection(update: Update, context: CallbackContext):
    """Handle international payment method selection"""
    query = update.callback_query
    data = query.data.split('_')
    payment_code = data[1]
    
    # Handle direct Wise payment
    if payment_code == "wise" and data[2] == "direct":
        amount = float(data[3])
        return handle_wise_direct(update, context, amount)
    
    # Normal flow for currency-specific payments
    amount = float(data[2])
    
    # Handle Wise currencies
    if payment_code in ["usd", "eur", "gbp", "aud", "aed", "cad"]:
        currency_info = INTERNATIONAL_PAYMENT_METHODS["wise"]["currencies"][payment_code]
        wise_info = INTERNATIONAL_PAYMENT_METHODS["wise"]
        
        # Calculate amount in local currency
        currency_code = currency_info['name']
        local_amount = amount
        if currency_code != "USD":
            local_amount = amount * CURRENCY_RATES.get(currency_code, 1)
        
        # Store payment info in context for later use
        context.user_data['payment_info'] = {
            'amount': amount,
            'amount_local': local_amount,
            'currency': currency_code,
            'bank': f"Wise {currency_info['flag']} {currency_info['name']}",
            'account': currency_info['details']
        }
        
        # Format the details in a cleaner way
        details_lines = currency_info['details'].split('\n')
        formatted_details = ""
        for line in details_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                if "number" in key.lower() or "iban" in key.lower() or "swift" in key.lower() or "code" in key.lower():
                    formatted_details += f"{key}: <code>{value.strip()}</code>\n"
                else:
                    formatted_details += f"{key}:{value}\n"
            else:
                formatted_details += f"{line}\n"
        
        method_name = f"{currency_info['flag']} Wise {currency_info['name']}"
        
        # Display amount in both USD and local currency
        amount_display = f"<code>${amount:.2f}</code>"
        if currency_code != "USD":
            amount_display += f" ({currency_code} {local_amount:.2f})"
        
        message = (
            f"🌐 <b>{method_name} Payment Details</b>\n\n"
            f"<b>Amount to pay:</b> {amount_display}\n\n"
            f"<b>Account Details:</b>\n"
            f"{formatted_details}\n"
            f"<b>Payment Instructions:</b>\n"
            f"1. Log in to your bank account\n"
            f"2. Make a transfer"
        )
        
        # Add specific currency instruction if not USD
        if currency_code != "USD":
            message += f" of <b>{currency_code} {local_amount:.2f}</b>"
        
        message += (
            " using the details above\n"
            f"3. Take a screenshot of the payment confirmation\n\n"
            f"After payment, click 'I've Paid' and send the screenshot when prompted."
        )
        
    # Handle Dukascopy
    elif payment_code == "dukascopy":
        payment_info = INTERNATIONAL_PAYMENT_METHODS["dukascopy"]
        
        # Store payment info in context for later use
        context.user_data['payment_info'] = {
            'amount': amount,
            'bank': payment_info['method'],
            'account': payment_info['details']
        }
        
        # Format the details in a cleaner way
        details_lines = payment_info['details'].split('\n')
        formatted_details = ""
        for line in details_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                if "account" in key.lower():
                    formatted_details += f"{key}: <code>{value.strip()}</code>\n"
                else:
                    formatted_details += f"{key}:{value}\n"
            else:
                formatted_details += f"{line}\n"
        
        method_name = payment_info['method']
        
        message = (
            f"🏦 <b>{method_name} Payment Details</b>\n\n"
            f"<b>Amount to pay:</b> <code>${amount:.2f}</code>\n\n"
            f"<b>Account Details:</b>\n"
            f"{formatted_details}\n"
            f"<b>Payment Instructions:</b>\n"
            f"1. Log in to your Dukascopy account\n"
            f"2. Make a transfer using the details above\n"
            f"3. Take a screenshot of the payment confirmation\n\n"
            f"After payment, click 'I've Paid' and send the screenshot when prompted."
        )
    else:
        query.answer("Invalid payment method")
        return ConversationHandler.END
    
    # Add "I've Paid" and "Back" buttons
    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"paid_intl_{payment_code}_{amount}")],
        [InlineKeyboardButton("🔙 Back to Options", callback_data="method_intl")],
        [InlineKeyboardButton("❌ Cancel", callback_data="method_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

def show_international_options_message(update: Update, context: CallbackContext, amount: float):
    """Show available international payment options - for direct message input"""
    message = (
        f"🌍 <b>International Payment Options</b>\n\n"
        f"Amount to pay: <code>${amount:.2f}</code>\n\n"
        f"Please choose your preferred payment method:"
    )
    
    # Create keyboard with international payment options
    keyboard = [
        [InlineKeyboardButton("🌐 Wise (Recommended)", callback_data=f"intl_wise_direct_{amount}")],
        [InlineKeyboardButton("🇺🇸 USD", callback_data=f"intl_usd_{amount}")],
        [InlineKeyboardButton("🇪🇺 EUR", callback_data=f"intl_eur_{amount}")],
        [InlineKeyboardButton("🇬🇧 GBP", callback_data=f"intl_gbp_{amount}")],
        [InlineKeyboardButton("🇦🇺 AUD", callback_data=f"intl_aud_{amount}")],
        [InlineKeyboardButton("🇦🇪 AED", callback_data=f"intl_aed_{amount}")],
        [InlineKeyboardButton("🇨🇦 CAD", callback_data=f"intl_cad_{amount}")],
        [InlineKeyboardButton("🏦 Dukascopy Bank", callback_data=f"intl_dukascopy_{amount}")],
        [InlineKeyboardButton("💬 Contact Admin Directly", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pay_back_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_html(
        message,
        reply_markup=reply_markup
    )

def show_crypto_options_message(update: Update, context: CallbackContext, amount: float):
    """Show available cryptocurrency payment options - for direct message input"""
    message = (
        f"₿ <b>Cryptocurrency Payment Options</b>\n\n"
        f"Amount to pay: <code>${amount:.2f}</code>\n\n"
        f"Please choose your preferred option:"
    )
    
    # Create simplified crypto options
    keyboard = [
        [InlineKeyboardButton("💰 Binance ID", callback_data=f"crypto_binance_{amount}")],
        [InlineKeyboardButton("💰 OKX UID", callback_data=f"crypto_okx_{amount}")],
        [InlineKeyboardButton("💰 Bybit UID", callback_data=f"crypto_bybit_{amount}")],
        [InlineKeyboardButton("💰 Mexc UID", callback_data=f"crypto_mexc_{amount}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pay_back_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_html(
        message,
        reply_markup=reply_markup
    )

def handle_wise_direct_message(update: Update, context: CallbackContext, amount: float):
    """Handle direct Wise payment - for direct message input"""
    # Store payment info in context for later use
    context.user_data['payment_info'] = {
        'amount': amount,
        'amount_local': amount,
        'currency': 'USD',
        'bank': "Wise Direct Payment",
        'account': "Direct payment via Wise"
    }
    
    # Get Wise payment details
    wise_info = INTERNATIONAL_PAYMENT_METHODS["wise"]
    
    # Format the details in a cleaner way
    formatted_details = (
        "Name: Munir Ayub\n"
        "Email: <code>munirayub011@gmail.com</code>\n"
        "Payment Link: <code>https://wise.com/pay/me/munirauubm</code>"
    )
    
    # Create the message
    message = (
        f"🌐 <b>Wise Direct Payment</b>\n\n"
        f"Amount to pay: <code>${amount:.2f}</code>\n\n"
        f"<b>Payment Details:</b>\n"
        f"{formatted_details}\n\n"
        f"<b>Instructions:</b>\n"
        f"1. Go to the Wise website or app\n"
        f"2. Send the exact amount of ${amount:.2f}\n"
        f"3. Add your Telegram ID <code>{update.effective_user.id}</code> in the reference/note\n"
        f"4. Take a screenshot of the payment confirmation\n"
        f"5. Click 'I've Paid' and send the screenshot when prompted"
    )
    
    # Create keyboard with confirmation and cancel buttons
    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"pay_confirm_wise_{amount}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"pay_back_{amount}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="pay_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_html(
        message,
        reply_markup=reply_markup
    )

# Create conversation handler
recharge_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('recharge', recharge_command),
        CallbackQueryHandler(handle_method_selection, pattern=r'^method_'),
        CallbackQueryHandler(handle_back_to_methods, pattern=r'^back_to_methods$'),
        CallbackQueryHandler(handle_recharge_callback, pattern=r'^recharge_'),
        CallbackQueryHandler(handle_payment_method, pattern=r'^pay_'),
        CallbackQueryHandler(handle_bank_selection, pattern=r'^bank_'),
        CallbackQueryHandler(handle_international_selection, pattern=r'^intl_'),
        CallbackQueryHandler(handle_crypto_selection, pattern=r'^crypto_'),
        CallbackQueryHandler(handle_paid_confirmation, pattern=r'^paid_'),
        CallbackQueryHandler(handle_verification, pattern=r'^verify_|^reject_')
    ],
    states={
        AMOUNT: [MessageHandler(Filters.text & ~Filters.command, handle_custom_amount)],
        RECEIPT: [MessageHandler(Filters.photo & ~Filters.command, handle_receipt_photo)]
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)

# No need for separate callback handlers since they're included in the conversation handler 