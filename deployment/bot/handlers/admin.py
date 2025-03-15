import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from utils.api_client import api_client
from utils.db import db
from utils.helpers import is_admin

# Define states
ADMIN_MENU, BROADCASTING, VIEWING_STATS, ADDING_BALANCE, REMOVING_BALANCE, ENTERING_USER_ID, ENTERING_BALANCE_AMOUNT, ENTERING_REFERRAL_SETTINGS, ENTERING_CURRENCY_RATE, MANAGING_SERVICE_PRICES, ENTERING_SERVICE_ID, ENTERING_SERVICE_PRICE, ENTERING_PRICE_RANGE, REMOVING_BALANCE_OPTIONS, BROADCAST_MEDIA_TYPE, BROADCAST_CONTENT, BROADCAST_COLLECTION = range(17)

# Module logger
logger = logging.getLogger(__name__)

def admin_command(update: Update, context: CallbackContext):
    """Handler for /admin command - only admins can use this"""
    user = update.effective_user
    
    # Check if user is admin
    if not is_admin(user.id):
        update.message.reply_text("❌ You don't have permission to use this command.")
        return ConversationHandler.END
    
    # Create admin menu
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 Manage Balance", callback_data="admin_manage_balance")],
        [InlineKeyboardButton("💱 Currency Rates", callback_data="admin_currency_rates")],
        [InlineKeyboardButton("🏷️ Service Prices", callback_data="admin_service_prices")],
        [InlineKeyboardButton("👥 Check User Referrals", callback_data="admin_check_user_referrals")],
        [InlineKeyboardButton("🎁 Referral Bonuses", callback_data="admin_referral_bonuses")],
        [InlineKeyboardButton("⚙️ Referral Settings", callback_data="admin_referral_settings")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("❌ Exit", callback_data="admin_exit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"👑 Admin Panel\n\n"
        f"Welcome to the admin panel, {user.first_name}.\n"
        f"Please select an option:",
        reply_markup=reply_markup
    )
    
    return ADMIN_MENU

def admin_menu_callback(update: Update, context: CallbackContext):
    """Handle admin menu callbacks"""
    query = update.callback_query
    query.answer()
    
    # Get selected option
    option = query.data
    
    if option == "admin_stats":
        # Show statistics
        return show_stats(update, context)
    
    elif option == "admin_view_all_users":
        # Show all users
        return show_all_users(update, context, page=1)
    
    elif option == "admin_view_active_users":
        # Show active users
        return show_active_users(update, context, page=1)
    
    elif option == "admin_view_all_orders":
        # Show all orders
        return show_all_orders(update, context, page=1)
    
    elif option == "admin_view_recent_orders":
        # Show recent orders
        return show_recent_orders(update, context, page=1)
    
    elif option.startswith("admin_users_page_"):
        # Handle user list pagination
        page = int(option.split("_")[-1])
        return show_all_users(update, context, page)
    
    elif option.startswith("admin_active_users_page_"):
        # Handle active user list pagination
        page = int(option.split("_")[-1])
        return show_active_users(update, context, page)
    
    elif option.startswith("admin_orders_page_"):
        # Handle order list pagination
        page = int(option.split("_")[-1])
        return show_all_orders(update, context, page)
    
    elif option.startswith("admin_recent_orders_page_"):
        # Handle recent order list pagination
        page = int(option.split("_")[-1])
        return show_recent_orders(update, context, page)
    
    elif option == "admin_broadcast":
        # Start broadcast flow
        keyboard = [
            [InlineKeyboardButton("📝 Text Message", callback_data="broadcast_type_text")],
            [InlineKeyboardButton("🖼️ Photo", callback_data="broadcast_type_photo")],
            [InlineKeyboardButton("🎬 Video", callback_data="broadcast_type_video")],
            [InlineKeyboardButton("🔊 Voice/Audio", callback_data="broadcast_type_audio")],
            [InlineKeyboardButton("📁 Document/File", callback_data="broadcast_type_document")],
            [InlineKeyboardButton("📱 Media Collection", callback_data="broadcast_type_collection")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "📢 Broadcast Message\n\n"
            "Please select the type of content you want to broadcast to all users:",
            reply_markup=reply_markup
        )
        return BROADCAST_MEDIA_TYPE
    
    elif option == "admin_manage_balance":
        # Show balance management options
        keyboard = [
            [InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance")],
            [InlineKeyboardButton("➖ Remove Balance", callback_data="admin_remove_balance")],
            [InlineKeyboardButton("👀 View User Balance", callback_data="admin_view_balance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "💰 Balance Management\n\n"
            "Select an action:",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    elif option == "admin_currency_rates":
        # Show currency rates management
        return show_currency_rates(update, context)
    
    elif option.startswith("admin_edit_rate_"):
        # Handle currency rate editing
        currency = option.replace("admin_edit_rate_", "")
        query.edit_message_text(
            f"💱 Edit Exchange Rate for {currency}\n\n"
            f"Please enter the new exchange rate for {currency}:\n"
            f"(Current rate will be shown on confirmation)"
        )
        context.user_data['edit_currency'] = currency
        return ENTERING_CURRENCY_RATE
    
    elif option == "admin_service_prices":
        # Show service price management options
        return show_service_price_options(update, context)
    
    elif option == "admin_edit_single_service":
        # Edit price for a single service
        query.edit_message_text(
            "🏷️ Edit Single Service Price\n\n"
            "Please enter the service ID to edit its price:"
        )
        return ENTERING_SERVICE_ID
    
    elif option == "admin_edit_price_range":
        # Edit prices for services in a price range
        return show_price_range_form(update, context)
    
    elif option == "admin_view_price_overrides":
        # View all price overrides
        return show_price_overrides(update, context)
    
    elif option.startswith("admin_reset_price_"):
        # Reset price for a service
        service_id = option.replace("admin_reset_price_", "")
        return reset_service_price(update, context, service_id)
    
    elif option == "admin_referral_bonuses":
        # Show pending referral bonuses
        return show_referral_bonuses(update, context)
    
    elif option == "admin_referral_settings":
        # Show referral settings
        return show_referral_settings(update, context)
    
    elif option == "admin_check_user_referrals":
        # Check user referrals
        query.edit_message_text(
            "👥 Check User Referrals\n\n"
            "Enter the user ID to check their referrals:"
        )
        context.user_data['admin_action'] = 'check_referrals'
        return ENTERING_USER_ID
    
    elif option == "admin_add_balance":
        # Start add balance flow
        query.edit_message_text(
            "➕ Add Balance\n\n"
            "Please enter the user ID to add balance to:"
        )
        context.user_data["admin_action"] = "add_balance"
        context.user_data["admin_target_user_id"] = None
        return ENTERING_USER_ID
    
    elif option == "admin_view_balance":
        # Start view balance flow
        query.edit_message_text(
            "👀 View Balance\n\n"
            "Enter the user ID to view balance:"
        )
        return ENTERING_USER_ID
    
    elif option == "admin_remove_balance":
        # Start remove balance flow
        query.edit_message_text(
            "➖ Remove Balance\n\n"
            "Please enter the user ID to remove balance from:"
        )
        context.user_data["admin_action"] = "remove_balance"
        context.user_data["admin_target_user_id"] = None
        return ENTERING_USER_ID
    
    elif option == "admin_back":
        # Go back to main admin menu
        user = update.effective_user
        
        # Create admin menu
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("💰 Manage Balance", callback_data="admin_manage_balance")],
            [InlineKeyboardButton("💱 Currency Rates", callback_data="admin_currency_rates")],
            [InlineKeyboardButton("🏷️ Service Prices", callback_data="admin_service_prices")],
            [InlineKeyboardButton("👥 Check User Referrals", callback_data="admin_check_user_referrals")],
            [InlineKeyboardButton("🎁 Referral Bonuses", callback_data="admin_referral_bonuses")],
            [InlineKeyboardButton("⚙️ Referral Settings", callback_data="admin_referral_settings")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("❌ Exit", callback_data="admin_exit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            f"👑 Admin Panel\n\n"
            f"Welcome to the admin panel, {user.first_name}.\n"
            f"Please select an option:",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    elif option == "admin_exit":
        # Exit admin panel
        query.edit_message_text("✅ Exited admin panel.")
        return ConversationHandler.END
    
    # Handle referral bonus actions
    elif option.startswith("admin_approve_bonus_"):
        bonus_id = option.split("_")[-1]
        return process_referral_bonus(update, context, bonus_id, "approved")
    
    elif option.startswith("admin_decline_bonus_"):
        bonus_id = option.split("_")[-1]
        return process_referral_bonus(update, context, bonus_id, "declined")
    
    # Handle user referral pagination
    elif option.startswith("ref_admin_page_"):
        # Extract page number and user_id
        parts = option.split("_")
        page = int(parts[3])
        user_id = int(parts[4])
        return show_user_referrals(update, context, user_id, page)
    
    # Handle referral settings actions
    elif option == "admin_set_referral_threshold":
        query.edit_message_text(
            "🔢 Set Referral Threshold\n\n"
            "Enter the number of referrals required to earn a bonus:"
        )
        context.user_data["admin_setting"] = "referral_threshold"
        return ENTERING_REFERRAL_SETTINGS
    
    elif option == "admin_set_bonus_amount":
        query.edit_message_text(
            "💵 Set Bonus Amount\n\n"
            "Enter the bonus amount in ETB:"
        )
        context.user_data["admin_setting"] = "bonus_amount"
        return ENTERING_REFERRAL_SETTINGS
    
    else:
        query.edit_message_text("❌ Invalid option.")
        return ConversationHandler.END

def show_stats(update: Update, context: CallbackContext):
    """Show bot statistics"""
    query = update.callback_query
    
    # Get statistics from database
    total_users = db.get_total_users()
    active_users = db.get_active_users(days=7)
    total_orders = db.get_total_orders()
    recent_orders = db.get_recent_orders(days=7)
    
    # Format statistics message
    stats_message = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"👤 Active Users (7d): {active_users}\n"
        f"📦 Total Orders: {total_orders}\n"
        f"📦 Recent Orders (7d): {recent_orders}\n"
    )
    
    # Create keyboard with detailed view buttons
    keyboard = [
        [InlineKeyboardButton("👥 View All Users", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("👤 View Active Users", callback_data="admin_view_active_users")],
        [InlineKeyboardButton("📦 View All Orders", callback_data="admin_view_all_orders")],
        [InlineKeyboardButton("📦 View Recent Orders", callback_data="admin_view_recent_orders")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(stats_message, reply_markup=reply_markup, parse_mode="HTML")
    
    return ADMIN_MENU

def handle_user_id_input(update: Update, context: CallbackContext):
    """Handle user ID or username input for various admin actions"""
    user_input = update.message.text.strip()
    
    # Check if input is a numeric ID or a username
    is_numeric = False
    try:
        user_id = int(user_input)
        is_numeric = True
    except ValueError:
        # Input might be a username
        pass
    
    # Look up user based on input type
    user_data = None
    if is_numeric:
        # Lookup by user ID
        user_data = db.get_user(user_id)
        if user_data:
            user_id = user_data['user_id']
    else:
        # Strip @ if present in username
        if user_input.startswith('@'):
            user_input = user_input[1:]
            
        # Lookup by username
        user_data = db.get_user_by_username(user_input)
        if user_data:
            user_id = user_data['user_id']
    
    if not user_data:
        update.message.reply_text(
            "❌ User not found. Please enter a valid user ID or username."
        )
        return ENTERING_USER_ID
    
    # Store user ID in context
    context.user_data['target_user_id'] = user_id
    context.user_data['target_user_data'] = user_data
    
    # Check which action we're performing
    admin_action = context.user_data.get('admin_action')
    
    if admin_action == 'add_balance':
        # Continue with add balance flow
        update.message.reply_text(
            f"User found: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
            f"Username: {user_data.get('username', 'None')}\n"
            f"Current balance: ${user_data.get('balance', 0):.6f}\n\n"
            f"Enter the amount to add to the user's balance:"
        )
        return ENTERING_BALANCE_AMOUNT
        
    elif admin_action == 'remove_balance':
        # Store user ID in context for later use
        context.user_data["admin_target_user_id"] = user_id
        current_balance = user_data.get('balance', 0)
        
        # Show remove balance options
        keyboard = [
            [InlineKeyboardButton("🧹 Remove All Balance", callback_data="admin_remove_all_balance")],
            [InlineKeyboardButton("🔢 Remove Custom Amount", callback_data="admin_remove_custom_balance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back_to_balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_html(
            f"User found: <b>{user_data.get('first_name', '')} {user_data.get('last_name', '')}</b>\n"
            f"Username: @{user_data.get('username', 'None')}\n"
            f"Current balance: <code>${current_balance:.2f}</code>\n\n"
            f"What would you like to do?",
            reply_markup=reply_markup
        )
        return REMOVING_BALANCE_OPTIONS
        
    elif admin_action == 'check_referrals':
        # Show user's referrals
        return show_user_referrals(update, context, user_id)
        
    else:
        # Unknown action
        update.message.reply_text("❌ Unknown action. Please try again.")
        return ConversationHandler.END

def handle_balance_amount(update: Update, context: CallbackContext):
    """Handle balance amount input for adding balance to a user"""
    target_user_id = context.user_data.get("admin_target_user_id")
    user_data = context.user_data.get('target_user_data')
    
    if not target_user_id or not user_data:
        update.message.reply_text("Error: No target user selected. Please try again.")
        return ConversationHandler.END
    
    # Get username for display
    username = user_data.get('username', 'None')
    username_display = f"@{username}" if username else "No username"
    
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            update.message.reply_text("Please enter a positive amount.")
            return ENTERING_BALANCE_AMOUNT
        
        # Store amount in context for confirmation
        context.user_data["admin_balance_amount"] = amount
        
        # Check if this is a balance addition or removal
        admin_action = context.user_data.get('admin_action')
        
        if admin_action == 'remove_balance':
            # Make sure the amount doesn't exceed current balance
            current_balance = user_data.get('balance', 0)
            if amount > current_balance:
                update.message.reply_text(
                    f"❌ Error: The amount to remove (${amount:.2f}) exceeds the user's current balance (${current_balance:.2f}).\n"
                    f"Please enter a smaller amount or use the 'Remove All Balance' option."
                )
                return ENTERING_BALANCE_AMOUNT
                
            # Create confirmation keyboard for removal
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_remove_balance"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_balance")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Show confirmation message for removal
            update.message.reply_html(
                f"💰 <b>Confirm Balance Removal</b>\n\n"
                f"User ID: <code>{target_user_id}</code>\n"
                f"Username: {username_display}\n"
                f"Current balance: <code>${current_balance:.2f}</code>\n"
                f"Amount to remove: <code>${amount:.2f}</code>\n"
                f"New balance will be: <code>${current_balance - amount:.2f}</code>\n\n"
                f"Are you sure you want to remove this balance?",
                reply_markup=reply_markup
            )
        else:
            # Create confirmation keyboard for addition
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_add_balance"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_balance")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Show confirmation message for addition
            update.message.reply_html(
                f"💰 <b>Confirm Balance Addition</b>\n\n"
                f"User ID: <code>{target_user_id}</code>\n"
                f"Username: {username_display}\n"
                f"Amount: <code>${amount:.2f}</code>\n\n"
                f"Are you sure you want to add this balance?",
                reply_markup=reply_markup
            )
        
        return ADMIN_MENU
        
    except ValueError:
        update.message.reply_text("Please enter a valid number.")
        return ENTERING_BALANCE_AMOUNT

def confirm_add_balance(update: Update, context: CallbackContext):
    """Handle balance addition confirmation"""
    query = update.callback_query
    query.answer()
    
    if query.data == "confirm_add_balance":
        target_user_id = context.user_data.get("admin_target_user_id")
        amount = context.user_data.get("admin_balance_amount")
        
        if not target_user_id or amount is None:
            query.edit_message_text("❌ Error: Missing user ID or amount. Please try again.")
            return ConversationHandler.END
        
        # Add balance to user's account
        if db.add_balance(target_user_id, amount, f"Admin balance addition by {update.effective_user.id}"):
            new_balance = db.get_balance(target_user_id)
            query.edit_message_text(
                f"✅ Successfully added ${amount:.2f} to user <code>{target_user_id}</code>\n"
                f"New balance: ${new_balance:.2f}",
                parse_mode="HTML"
            )
        else:
            query.edit_message_text("❌ Failed to add balance. Please try again.")
    else:
        query.edit_message_text("❌ Balance addition cancelled.")
    
    # Clear the stored data
    context.user_data.pop("admin_target_user_id", None)
    context.user_data.pop("admin_balance_amount", None)
    
    return ConversationHandler.END

def confirm_remove_balance(update: Update, context: CallbackContext):
    """Handle balance removal confirmation"""
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "confirm_remove_balance":
        target_user_id = context.user_data.get("admin_target_user_id")
        amount = context.user_data.get("admin_balance_amount")
        
        if not target_user_id or amount is None:
            query.edit_message_text("❌ Error: Missing user ID or amount. Please try again.")
            return ConversationHandler.END
        
        # Remove balance from user's account
        if db.deduct_balance(target_user_id, amount, f"Admin balance removal by {user_id}"):
            new_balance = db.get_balance(target_user_id)
            query.edit_message_text(
                f"✅ Successfully removed ${amount:.2f} from user <code>{target_user_id}</code>\n"
                f"New balance: ${new_balance:.2f}",
                parse_mode="HTML"
            )
        else:
            query.edit_message_text("❌ Failed to remove balance. Please try again.")
    
    elif query.data == "confirm_remove_all_balance":
        target_user_id = context.user_data.get("admin_target_user_id")
        
        if not target_user_id:
            query.edit_message_text("❌ Error: Missing user ID. Please try again.")
            return ConversationHandler.END
        
        # Get current balance
        current_balance = db.get_balance(target_user_id)
        
        # Remove all balance from user's account
        if current_balance > 0:
            if db.deduct_balance(target_user_id, current_balance, f"Admin full balance removal by {user_id}"):
                query.edit_message_text(
                    f"✅ Successfully removed all balance (${current_balance:.2f}) from user <code>{target_user_id}</code>\n"
                    f"New balance: $0.00",
                    parse_mode="HTML"
                )
            else:
                query.edit_message_text("❌ Failed to remove balance. Please try again.")
        else:
            query.edit_message_text(
                f"ℹ️ User <code>{target_user_id}</code> already has $0.00 balance. No action taken.",
                parse_mode="HTML"
            )
    
    elif query.data == "cancel_remove_balance":
        query.edit_message_text("❌ Balance removal cancelled.")
    
    # Clear the stored data
    context.user_data.pop("admin_target_user_id", None)
    context.user_data.pop("admin_balance_amount", None)
    context.user_data.pop("target_user_data", None)
    
    return ConversationHandler.END

def handle_remove_balance_options(update: Update, context: CallbackContext):
    """Handle remove balance option selection"""
    query = update.callback_query
    query.answer()
    
    option = query.data
    target_user_id = context.user_data.get("admin_target_user_id")
    user_data = context.user_data.get('target_user_data')
    
    if not target_user_id or not user_data:
        query.edit_message_text("❌ Error: No user selected. Please try again.")
        return ConversationHandler.END
    
    current_balance = user_data.get('balance', 0)
    username = user_data.get('username', 'None')
    username_display = f"@{username}" if username else "No username"
    
    if option == "admin_remove_all_balance":
        # Create confirmation keyboard for removing all balance
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_remove_all_balance"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_balance")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            f"💰 <b>Confirm Full Balance Removal</b>\n\n"
            f"User ID: <code>{target_user_id}</code>\n"
            f"Username: {username_display}\n"
            f"Current balance: <code>${current_balance:.2f}</code>\n\n"
            f"Are you sure you want to remove ALL balance from this user?",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return ADMIN_MENU
        
    elif option == "admin_remove_custom_balance":
        # Ask for custom amount to remove
        query.edit_message_text(
            f"💰 <b>Remove Custom Balance Amount</b>\n\n"
            f"User ID: <code>{target_user_id}</code>\n"
            f"Current balance: <code>${current_balance:.2f}</code>\n\n"
            f"Enter the amount to remove from the user's balance:",
            parse_mode="HTML"
        )
        return ENTERING_BALANCE_AMOUNT
        
    elif option == "admin_back_to_balance":
        # Go back to balance management
        keyboard = [
            [InlineKeyboardButton("➕ Add Balance", callback_data="admin_add_balance")],
            [InlineKeyboardButton("➖ Remove Balance", callback_data="admin_remove_balance")],
            [InlineKeyboardButton("👀 View User Balance", callback_data="admin_view_balance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "💰 Balance Management\n\n"
            "Select an action:",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    return ADMIN_MENU

def handle_remove_balance_amount(update: Update, context: CallbackContext):
    """Handle balance amount input for removing balance from a user"""
    target_user_id = context.user_data.get("admin_target_user_id")
    user_data = context.user_data.get('target_user_data')
    
    if not target_user_id or not user_data:
        update.message.reply_text("Error: No target user selected. Please try again.")
        return ConversationHandler.END
    
    current_balance = user_data.get('balance', 0)
    
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            update.message.reply_text("Please enter a positive amount.")
            return ENTERING_BALANCE_AMOUNT
            
        if amount > current_balance:
            update.message.reply_text(
                f"❌ Error: The amount to remove (${amount:.2f}) exceeds the user's current balance (${current_balance:.2f}).\n"
                f"Please enter a smaller amount or use the 'Remove All Balance' option."
            )
            return ENTERING_BALANCE_AMOUNT
        
        # Store amount in context for confirmation
        context.user_data["admin_balance_amount"] = amount
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_remove_balance"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_balance")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show confirmation message
        update.message.reply_html(
            f"💰 <b>Confirm Balance Removal</b>\n\n"
            f"User ID: <code>{target_user_id}</code>\n"
            f"Current balance: <code>${current_balance:.2f}</code>\n"
            f"Amount to remove: <code>${amount:.2f}</code>\n"
            f"New balance will be: <code>${current_balance - amount:.2f}</code>\n\n"
            f"Are you sure you want to remove this balance?",
            reply_markup=reply_markup
        )
        
        return ADMIN_MENU
        
    except ValueError:
        update.message.reply_text("Please enter a valid number.")
        return ENTERING_BALANCE_AMOUNT

def handle_broadcast_media_type(update: Update, context: CallbackContext):
    """Handle selection of broadcast media type"""
    query = update.callback_query
    query.answer()
    
    # Get selected media type
    media_type = query.data.replace("broadcast_type_", "")
    
    # Store media type in context
    context.user_data["broadcast_media_type"] = media_type
    
    if media_type == "text":
        query.edit_message_text(
            "📝 Broadcast Text Message\n\n"
            "Please enter the message you want to send to all users:\n\n"
            "You can include:\n"
            "- Regular text\n"
            "- HTML formatting (<b>bold</b>, <i>italic</i>, etc.)\n"
            "- URLs will be automatically detected\n\n"
            "Type your message:"
        )
        return BROADCASTING
    
    elif media_type == "photo":
        query.edit_message_text(
            "🖼️ Broadcast Photo\n\n"
            "Please send the photo you want to broadcast to all users.\n"
            "You can also add a caption with the photo."
        )
        return BROADCASTING
    
    elif media_type == "video":
        query.edit_message_text(
            "🎬 Broadcast Video\n\n"
            "Please send the video you want to broadcast to all users.\n"
            "You can also add a caption with the video."
        )
        return BROADCASTING
    
    elif media_type == "audio":
        query.edit_message_text(
            "🔊 Broadcast Voice/Audio\n\n"
            "Please send the voice message or audio file you want to broadcast to all users.\n"
            "You can also add a caption with the audio."
        )
        return BROADCASTING
    
    elif media_type == "document":
        query.edit_message_text(
            "📁 Broadcast Document/File\n\n"
            "Please send the document or file you want to broadcast to all users.\n"
            "You can also add a caption with the file."
        )
        return BROADCASTING
        
    elif media_type == "collection":
        # Initialize collection in context
        context.user_data["broadcast_collection"] = []
        
        # Show collection menu
        return show_broadcast_collection_menu(update, context)
    
    else:
        query.edit_message_text("❌ Invalid option selected.")
        return ConversationHandler.END

def show_broadcast_collection_menu(update: Update, context: CallbackContext):
    """Show menu for creating a collection of media items to broadcast"""
    query = update.callback_query
    
    # Get current collection
    collection = context.user_data.get("broadcast_collection", [])
    collection_size = len(collection)
    
    # Create message showing current collection
    message = f"📱 <b>Media Collection</b> ({collection_size} items)\n\n"
    
    if collection:
        message += "<b>Current items:</b>\n"
        for i, item in enumerate(collection, 1):
            item_type = item.get("type", "unknown")
            caption = item.get("caption", "")
            if item_type == "text":
                preview = item.get("text", "")[:50] + "..." if len(item.get("text", "")) > 50 else item.get("text", "")
                message += f"{i}. 📝 Text: {preview}\n"
            elif item_type == "photo":
                message += f"{i}. 🖼️ Photo" + (f" with caption: {caption[:20]}..." if caption else "") + "\n"
            elif item_type == "video":
                message += f"{i}. 🎬 Video" + (f" with caption: {caption[:20]}..." if caption else "") + "\n"
            elif item_type == "audio":
                message += f"{i}. 🔊 Audio" + (f" with caption: {caption[:20]}..." if caption else "") + "\n"
            elif item_type == "document":
                message += f"{i}. 📁 Document" + (f" with caption: {caption[:20]}..." if caption else "") + "\n"
    else:
        message += "Your collection is empty. Add some items to create your broadcast.\n"
    
    message += "\nWhat would you like to add to your collection?"
    
    # Create keyboard with options
    keyboard = [
        [InlineKeyboardButton("📝 Add Text", callback_data="add_collection_text")],
        [InlineKeyboardButton("🖼️ Add Photo", callback_data="add_collection_photo")],
        [InlineKeyboardButton("🎬 Add Video", callback_data="add_collection_video")],
        [InlineKeyboardButton("🔊 Add Audio", callback_data="add_collection_audio")],
        [InlineKeyboardButton("📁 Add Document", callback_data="add_collection_document")]
    ]
    
    # Add send options if collection has items
    if collection:
        keyboard.append([
            InlineKeyboardButton("📤 Preview & Send", callback_data="preview_collection"),
            InlineKeyboardButton("🗑 Clear All", callback_data="clear_collection")
        ])
        if collection_size > 1:
            keyboard.append([
                InlineKeyboardButton("📤 Send as Separate Messages", callback_data="send_separate"),
                InlineKeyboardButton("📤 Send as Group", callback_data="send_group")
            ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_broadcast")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_html(message, reply_markup=reply_markup)
    
    return BROADCAST_COLLECTION

def handle_broadcast_collection_action(update: Update, context: CallbackContext):
    """Handle actions for broadcast collection"""
    query = update.callback_query
    query.answer()
    
    action = query.data
    
    if action.startswith("add_collection_"):
        # Set the current action for adding to collection
        media_type = action.replace("add_collection_", "")
        context.user_data["collection_action"] = f"add_{media_type}"
        
        # Show appropriate message based on media type
        if media_type == "text":
            query.edit_message_text(
                "📝 Add Text to Collection\n\n"
                "Please enter the text message you want to add to your collection:\n\n"
                "You can include:\n"
                "- Regular text\n"
                "- HTML formatting (<b>bold</b>, <i>italic</i>, etc.)\n"
                "- URLs will be automatically detected\n\n"
                "Type your message:"
            )
        elif media_type == "photo":
            query.edit_message_text(
                "🖼️ Add Photo to Collection\n\n"
                "Please send the photo you want to add to your collection.\n"
                "You can also add a caption with the photo."
            )
        elif media_type == "video":
            query.edit_message_text(
                "🎬 Add Video to Collection\n\n"
                "Please send the video you want to add to your collection.\n"
                "You can also add a caption with the video."
            )
        elif media_type == "audio":
            query.edit_message_text(
                "🔊 Add Audio to Collection\n\n"
                "Please send the voice message or audio file you want to add to your collection.\n"
                "You can also add a caption with the audio."
            )
        elif media_type == "document":
            query.edit_message_text(
                "📁 Add Document to Collection\n\n"
                "Please send the document or file you want to add to your collection.\n"
                "You can also add a caption with the document."
            )
        
        return BROADCASTING
    
    elif action == "preview_collection":
        # Show preview of the collection
        return preview_broadcast_collection(update, context)
    
    elif action == "clear_collection":
        # Clear the collection
        context.user_data["broadcast_collection"] = []
        return show_broadcast_collection_menu(update, context)
    
    elif action == "send_separate":
        # Confirm sending as separate messages
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_send_separate"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_send")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        collection = context.user_data.get("broadcast_collection", [])
        query.edit_message_text(
            f"📤 <b>Send as Separate Messages</b>\n\n"
            f"You are about to send {len(collection)} separate messages to all users.\n"
            f"This will send each item in your collection as an individual message.\n\n"
            f"Are you sure you want to proceed?",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return BROADCAST_COLLECTION
    
    elif action == "send_group":
        # Confirm sending as a group
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_send_group"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_send")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        collection = context.user_data.get("broadcast_collection", [])
        query.edit_message_text(
            f"📤 <b>Send as Group</b>\n\n"
            f"You are about to send your collection as a media group to all users.\n"
            f"This works best for collections of photos and videos (up to 10 items).\n"
            f"Note: Text-only items will be skipped in group mode.\n\n"
            f"Are you sure you want to proceed?",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return BROADCAST_COLLECTION
    
    elif action == "confirm_send_separate":
        # Send collection as separate messages
        return send_broadcast_collection_separate(update, context)
    
    elif action == "confirm_send_group":
        # Send collection as a group
        return send_broadcast_collection_group(update, context)
    
    elif action == "cancel_send":
        # Cancel sending and go back to collection menu
        return show_broadcast_collection_menu(update, context)
    
    elif action == "admin_broadcast":
        # Go back to broadcast menu
        keyboard = [
            [InlineKeyboardButton("📝 Text Message", callback_data="broadcast_type_text")],
            [InlineKeyboardButton("🖼️ Photo", callback_data="broadcast_type_photo")],
            [InlineKeyboardButton("🎬 Video", callback_data="broadcast_type_video")],
            [InlineKeyboardButton("🔊 Voice/Audio", callback_data="broadcast_type_audio")],
            [InlineKeyboardButton("📁 Document/File", callback_data="broadcast_type_document")],
            [InlineKeyboardButton("📱 Media Collection", callback_data="broadcast_type_collection")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "📢 Broadcast Message\n\n"
            "Please select the type of content you want to broadcast to all users:",
            reply_markup=reply_markup
        )
        return BROADCAST_MEDIA_TYPE
    
    else:
        # Unknown action
        return show_broadcast_collection_menu(update, context)

def preview_broadcast_collection(update: Update, context: CallbackContext):
    """Show preview of broadcast collection and confirm sending"""
    query = update.callback_query
    
    collection = context.user_data.get("broadcast_collection", [])
    
    if not collection:
        query.edit_message_text(
            "❌ Collection is empty. Please add some items before previewing."
        )
        return show_broadcast_collection_menu(update, context)
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Send to All Users", callback_data="confirm_send_separate"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_send")
        ],
        [InlineKeyboardButton("⬅️ Back to Collection", callback_data="back_to_collection")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Create preview message
    message = "📤 <b>Broadcast Preview</b>\n\n"
    message += f"Your collection contains {len(collection)} items:\n\n"
    
    for i, item in enumerate(collection, 1):
        item_type = item.get("type", "unknown")
        caption = item.get("caption", "")
        if item_type == "text":
            preview = item.get("text", "")[:100] + "..." if len(item.get("text", "")) > 100 else item.get("text", "")
            message += f"{i}. 📝 <b>Text:</b> {preview}\n\n"
        elif item_type == "photo":
            message += f"{i}. 🖼️ <b>Photo</b>" + (f" with caption: {caption[:50]}..." if caption else "") + "\n\n"
        elif item_type == "video":
            message += f"{i}. 🎬 <b>Video</b>" + (f" with caption: {caption[:50]}..." if caption else "") + "\n\n"
        elif item_type == "audio":
            message += f"{i}. 🔊 <b>Audio</b>" + (f" with caption: {caption[:50]}..." if caption else "") + "\n\n"
        elif item_type == "document":
            message += f"{i}. 📁 <b>Document</b>" + (f" with caption: {caption[:50]}..." if caption else "") + "\n\n"
    
    message += "You can send these items as separate messages or as a group (photos and videos only).\n"
    message += "Are you ready to broadcast this collection to all users?"
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return BROADCAST_COLLECTION

def broadcast_message(update: Update, context: CallbackContext):
    """Process broadcast content from admin"""
    media_type = context.user_data.get("broadcast_media_type", "text")
    collection_action = context.user_data.get("collection_action", None)
    
    # Check if this is an addition to a collection
    if collection_action and collection_action.startswith("add_"):
        # This is an addition to a collection
        item_type = collection_action.replace("add_", "")
        
        # Initialize collection if not exists
        if "broadcast_collection" not in context.user_data:
            context.user_data["broadcast_collection"] = []
        
        # Add item to collection based on type
        if item_type == "text" and update.message.text:
            context.user_data["broadcast_collection"].append({
                "type": "text",
                "text": update.message.text
            })
            
        elif item_type == "photo" and update.message.photo:
            context.user_data["broadcast_collection"].append({
                "type": "photo",
                "file_id": update.message.photo[-1].file_id,
                "caption": update.message.caption or ""
            })
            
        elif item_type == "video" and update.message.video:
            context.user_data["broadcast_collection"].append({
                "type": "video",
                "file_id": update.message.video.file_id,
                "caption": update.message.caption or ""
            })
            
        elif item_type == "audio" and (update.message.voice or update.message.audio):
            file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
            context.user_data["broadcast_collection"].append({
                "type": "audio",
                "file_id": file_id,
                "caption": update.message.caption or ""
            })
            
        elif item_type == "document" and update.message.document:
            context.user_data["broadcast_collection"].append({
                "type": "document",
                "file_id": update.message.document.file_id,
                "caption": update.message.caption or ""
            })
            
        else:
            # Invalid content for selected media type
            update.message.reply_text(
                f"❌ Error: The content you sent doesn't match the selected type ({item_type}).\n"
                f"Please try again with the correct content type."
            )
            return BROADCASTING
        
        # Clear collection action
        context.user_data.pop("collection_action", None)
        
        # Show success message and return to collection menu
        update.message.reply_text(f"✅ Added {item_type} to your collection!")
        return show_broadcast_collection_menu(update, context)
    
    # Handle regular broadcast (not collection)
    else:
        # Store content based on media type
        if media_type == "text" and update.message.text:
            # Store text message
            context.user_data["broadcast_content"] = {
                "type": "text",
                "text": update.message.text
            }
        
        elif media_type == "photo" and update.message.photo:
            # Store photo and caption
            context.user_data["broadcast_content"] = {
                "type": "photo",
                "file_id": update.message.photo[-1].file_id,  # Get highest resolution
                "caption": update.message.caption or ""
            }
        
        elif media_type == "video" and update.message.video:
            # Store video and caption
            context.user_data["broadcast_content"] = {
                "type": "video",
                "file_id": update.message.video.file_id,
                "caption": update.message.caption or ""
            }
        
        elif media_type == "audio" and (update.message.voice or update.message.audio):
            # Store voice or audio and caption
            file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
            context.user_data["broadcast_content"] = {
                "type": "audio",
                "file_id": file_id,
                "caption": update.message.caption or ""
            }
        
        elif media_type == "document" and update.message.document:
            # Store document and caption
            context.user_data["broadcast_content"] = {
                "type": "document",
                "file_id": update.message.document.file_id,
                "caption": update.message.caption or ""
            }
        
        else:
            # Invalid content for selected media type
            update.message.reply_text(
                f"❌ Error: The content you sent doesn't match the selected media type ({media_type}).\n"
                f"Please try again or use /admin to go back to the admin panel."
            )
            return BROADCASTING
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Send", callback_data="broadcast_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show confirmation message based on media type
        if media_type == "text":
            update.message.reply_html(
                f"📢 <b>Broadcast Preview</b>\n\n"
                f"{context.user_data['broadcast_content']['text']}\n\n"
                f"Are you sure you want to send this message to all users?",
                reply_markup=reply_markup
            )
        else:
            caption = context.user_data["broadcast_content"].get("caption", "")
            update.message.reply_text(
                f"📢 Broadcast Preview\n\n"
                f"Media Type: {media_type.capitalize()}\n"
                f"Caption: {caption}\n\n"
                f"Are you sure you want to send this to all users?",
                reply_markup=reply_markup
            )
        
        return ADMIN_MENU

def send_broadcast_collection_separate(update: Update, context: CallbackContext):
    """Send broadcast collection as separate messages"""
    query = update.callback_query
    
    # Get collection from context
    collection = context.user_data.get("broadcast_collection", [])
    
    if not collection:
        query.edit_message_text("❌ Collection is empty. Nothing to send.")
        return ConversationHandler.END
    
    # Get all users from database
    users = db.get_all_users_list()
    
    if not users:
        query.edit_message_text("❌ No users found to broadcast to.")
        return ConversationHandler.END
    
    # Send each item in collection to all users
    success_count = 0
    fail_count = 0
    total_messages = len(collection) * len(users)
    
    # Show processing message
    query.edit_message_text(
        f"⏳ Processing broadcast...\n"
        f"Sending {len(collection)} messages to {len(users)} users ({total_messages} total messages).\n"
        f"This may take some time."
    )
    
    for user in users:
        user_id = user.get('user_id')
        user_success = 0
        
        for item in collection:
            item_type = item.get("type", "")
            try:
                if item_type == "text":
                    context.bot.send_message(
                        chat_id=user_id,
                        text=item.get("text", ""),
                        parse_mode="HTML"
                    )
                
                elif item_type == "photo":
                    context.bot.send_photo(
                        chat_id=user_id,
                        photo=item.get("file_id", ""),
                        caption=item.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif item_type == "video":
                    context.bot.send_video(
                        chat_id=user_id,
                        video=item.get("file_id", ""),
                        caption=item.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif item_type == "audio":
                    context.bot.send_audio(
                        chat_id=user_id,
                        audio=item.get("file_id", ""),
                        caption=item.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif item_type == "document":
                    context.bot.send_document(
                        chat_id=user_id,
                        document=item.get("file_id", ""),
                        caption=item.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                user_success += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast item to user {user_id}: {e}")
                fail_count += 1
        
        # If all messages were sent successfully to this user
        if user_success == len(collection):
            success_count += 1
    
    # Show results
    query.edit_message_text(
        f"✅ Broadcast complete!\n\n"
        f"📊 Results:\n"
        f"✓ Successfully delivered to: {success_count} users\n"
        f"✗ Failed deliveries: {fail_count} messages\n"
        f"📦 Total items sent: {len(collection)} per user\n\n"
        f"Use /admin to return to the admin panel."
    )
    
    # Clear broadcast data
    if "broadcast_collection" in context.user_data:
        del context.user_data["broadcast_collection"]
    
    return ConversationHandler.END

def send_broadcast_collection_group(update: Update, context: CallbackContext):
    """Send broadcast collection as a media group"""
    query = update.callback_query
    
    # Get collection from context
    collection = context.user_data.get("broadcast_collection", [])
    
    if not collection:
        query.edit_message_text("❌ Collection is empty. Nothing to send.")
        return ConversationHandler.END
    
    # Filter collection to include only media items (photos and videos)
    media_items = [item for item in collection if item.get("type") in ["photo", "video"]]
    
    if not media_items:
        query.edit_message_text(
            "❌ No suitable media items found for a media group.\n"
            "Media groups can only contain photos and videos."
        )
        return ConversationHandler.END
    
    # Limit to 10 items (Telegram API limit for media groups)
    if len(media_items) > 10:
        media_items = media_items[:10]
        query.edit_message_text(
            "⚠️ Your collection has more than 10 items.\n"
            "Only the first 10 items will be included in the media group (Telegram limit)."
        )
    
    # Get all users from database
    users = db.get_all_users_list()
    
    if not users:
        query.edit_message_text("❌ No users found to broadcast to.")
        return ConversationHandler.END
    
    # Prepare media group
    media_group = []
    for item in media_items:
        item_type = item.get("type", "")
        file_id = item.get("file_id", "")
        caption = item.get("caption", "")
        
        if item_type == "photo":
            media_group.append(InputMediaPhoto(media=file_id, caption=caption, parse_mode="HTML"))
        elif item_type == "video":
            media_group.append(InputMediaVideo(media=file_id, caption=caption, parse_mode="HTML"))
    
    # Show processing message
    query.edit_message_text(
        f"⏳ Processing broadcast...\n"
        f"Sending a media group with {len(media_group)} items to {len(users)} users.\n"
        f"This may take some time."
    )
    
    # Send media group to all users
    success_count = 0
    fail_count = 0
    
    for user in users:
        user_id = user.get('user_id')
        try:
            context.bot.send_media_group(
                chat_id=user_id,
                media=media_group
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send media group to user {user_id}: {e}")
            fail_count += 1
    
    # Check if there are text items that weren't included in the media group
    text_items = [item for item in collection if item.get("type") == "text"]
    
    # Show results
    result_message = (
        f"✅ Broadcast complete!\n\n"
        f"📊 Results:\n"
        f"✓ Successfully delivered to: {success_count} users\n"
        f"✗ Failed deliveries: {fail_count} users\n"
        f"📦 Media group items: {len(media_group)}\n"
    )
    
    if text_items:
        result_message += f"ℹ️ {len(text_items)} text items were not included in the media group.\n"
    
    result_message += "\nUse /admin to return to the admin panel."
    
    query.edit_message_text(result_message)
    
    # Clear broadcast data
    if "broadcast_collection" in context.user_data:
        del context.user_data["broadcast_collection"]
    
    return ConversationHandler.END

def broadcast_confirm(update: Update, context: CallbackContext):
    """Handle broadcast confirmation"""
    query = update.callback_query
    query.answer()
    
    if query.data == "broadcast_confirm":
        # Get the broadcast content from user_data
        broadcast_content = context.user_data.get("broadcast_content", {})
        
        if not broadcast_content:
            query.edit_message_text("⚠️ Broadcast content not found.")
            return ConversationHandler.END
        
        # Get all users from database
        users = db.get_all_users_list()
        
        if not users:
            query.edit_message_text("⚠️ No users found to broadcast to.")
            return ConversationHandler.END
        
        # Send message to all users based on content type
        success_count = 0
        fail_count = 0
        
        media_type = broadcast_content.get("type", "text")
        
        # Show processing message
        query.edit_message_text(
            f"⏳ Processing broadcast...\n"
            f"Sending {media_type} to {len(users)} users.\n"
            f"This may take some time."
        )
        
        for user in users:
            user_id = user.get('user_id')
            try:
                if media_type == "text":
                    context.bot.send_message(
                        chat_id=user_id,
                        text=broadcast_content["text"],
                        parse_mode="HTML"
                    )
                
                elif media_type == "photo":
                    context.bot.send_photo(
                        chat_id=user_id,
                        photo=broadcast_content["file_id"],
                        caption=broadcast_content.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif media_type == "video":
                    context.bot.send_video(
                        chat_id=user_id,
                        video=broadcast_content["file_id"],
                        caption=broadcast_content.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif media_type == "audio":
                    context.bot.send_audio(
                        chat_id=user_id,
                        audio=broadcast_content["file_id"],
                        caption=broadcast_content.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                elif media_type == "document":
                    context.bot.send_document(
                        chat_id=user_id,
                        document=broadcast_content["file_id"],
                        caption=broadcast_content.get("caption", ""),
                        parse_mode="HTML"
                    )
                
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user_id}: {e}")
                fail_count += 1
        
        # Show results
        query.edit_message_text(
            f"✅ Broadcast sent!\n\n"
            f"📊 Results:\n"
            f"✓ Sent successfully: {success_count}\n"
            f"✗ Failed: {fail_count}"
        )
    else:
        # Cancel broadcast
        query.edit_message_text("❌ Broadcast canceled.")
    
    # Clear broadcast data
    if "broadcast_content" in context.user_data:
        del context.user_data["broadcast_content"]
    if "broadcast_media_type" in context.user_data:
        del context.user_data["broadcast_media_type"]
    if "broadcast_collection" in context.user_data:
        del context.user_data["broadcast_collection"]
    
    return ConversationHandler.END

def cancel_command(update: Update, context: CallbackContext):
    """Cancel the current operation and clear user data"""
    if update.message:
        update.message.reply_text("Operation cancelled.")
    elif update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text("Operation cancelled.")
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END 

def show_referral_bonuses(update: Update, context: CallbackContext):
    """Show pending referral bonuses"""
    query = update.callback_query
    
    # Get pending bonuses
    pending_bonuses = db.get_pending_referral_bonuses()
    
    if not pending_bonuses:
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "🎁 Referral Bonuses\n\n"
            "No pending referral bonuses found.",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    # Create message with pending bonuses
    message = "🎁 <b>Pending Referral Bonuses</b>\n\n"
    
    for i, bonus in enumerate(pending_bonuses[:10], 1):  # Show max 10 bonuses at a time
        user_display = bonus['username'] if bonus['username'] else f"{bonus['first_name']} {bonus['last_name']}".strip()
        if not user_display:
            user_display = f"User {bonus['user_id']}"
        
        message += (
            f"{i}. <b>User:</b> {user_display} (ID: {bonus['user_id']})\n"
            f"   <b>Referrals:</b> {bonus['referral_count']}\n"
            f"   <b>Bonus:</b> ETB {bonus['bonus_amount']:.2f}\n"
            f"   <b>Created:</b> {bonus['created_at']}\n\n"
        )
    
    # Create keyboard with approve/decline buttons for each bonus
    keyboard = []
    for bonus in pending_bonuses[:10]:
        keyboard.append([
            InlineKeyboardButton(f"✅ Approve #{bonus['id']}", callback_data=f"admin_approve_bonus_{bonus['id']}"),
            InlineKeyboardButton(f"❌ Decline #{bonus['id']}", callback_data=f"admin_decline_bonus_{bonus['id']}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def process_referral_bonus(update: Update, context: CallbackContext, bonus_id, status):
    """Process a referral bonus (approve or decline)"""
    query = update.callback_query
    admin_id = query.from_user.id
    
    # Process the bonus
    success = db.process_referral_bonus(bonus_id, status, admin_id)
    
    if success:
        # Get the user ID for notification
        cursor = db.conn.cursor()
        cursor.execute('SELECT user_id FROM referral_bonuses WHERE id = ?', (bonus_id,))
        user_id = cursor.fetchone()[0]
        
        # Notify the user
        try:
            if status == "approved":
                context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 <b>Referral Bonus Approved!</b>\n\n"
                         "Your referral bonus of ETB 50 has been approved and added to your balance.\n"
                         "Thank you for inviting friends to our service!",
                    parse_mode="HTML"
                )
            else:
                context.bot.send_message(
                    chat_id=user_id,
                    text="ℹ️ <b>Referral Bonus Update</b>\n\n"
                         "Unfortunately, your referral bonus request could not be approved at this time.\n"
                         "Please contact support if you have any questions.",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error notifying user about bonus: {e}")
        
        # Show success message and return to bonus list
        query.answer(f"Bonus {status} successfully!")
        return show_referral_bonuses(update, context)
    else:
        # Show error message
        query.answer(f"Error processing bonus!")
        return show_referral_bonuses(update, context)

def show_referral_settings(update: Update, context: CallbackContext):
    """Show and manage referral bonus settings"""
    query = update.callback_query
    
    try:
        # Get current settings
        current_threshold_str = db.get_setting("referral_threshold", "50")  # Default to "50"
        current_amount_str = db.get_setting("bonus_amount", "50.0")  # Default to "50.0"
        
        try:
            # Convert to appropriate types for display
            current_threshold = int(current_threshold_str)
            current_amount = float(current_amount_str)
        except (ValueError, TypeError):
            # Use defaults if conversion fails
            current_threshold = 50
            current_amount = 50.0
            logger.warning(f"Failed to convert referral settings to numeric types. Using defaults: threshold={current_threshold}, amount={current_amount}")
        
        # Create message with current settings
        message = (
            f"⚙️ <b>Referral Bonus Settings</b>\n\n"
            f"<b>Current Settings:</b>\n"
            f"• <b>Referrals Required:</b> {current_threshold}\n"
            f"• <b>Bonus Amount:</b> ETB {current_amount:.2f}\n\n"
            f"These settings control when users earn referral bonuses:\n"
            f"- Users will earn a bonus of ETB {current_amount:.2f} for every {current_threshold} valid referrals\n"
            f"- Only referrals with a username are counted as valid\n\n"
            f"<b>Select a setting to change:</b>"
        )
        
        # Create keyboard with options
        keyboard = [
            [InlineKeyboardButton("🔢 Change Referral Threshold", callback_data="admin_set_referral_threshold")],
            [InlineKeyboardButton("💵 Change Bonus Amount", callback_data="admin_set_bonus_amount")],
            [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        
        return ADMIN_MENU
    except Exception as e:
        logger.error(f"Error in show_referral_settings: {e}")
        query.edit_message_text(
            f"❌ An error occurred while loading referral settings.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again later.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]])
        )
        return ADMIN_MENU

def handle_referral_settings_input(update: Update, context: CallbackContext):
    """Process referral settings input from admin"""
    setting_type = context.user_data.get("admin_setting")
    
    if not setting_type:
        update.message.reply_text("❌ Error: Setting type not specified.")
        return ConversationHandler.END
    
    try:
        if setting_type == "referral_threshold":
            # Parse threshold value
            input_text = update.message.text.strip()
            try:
                threshold = int(input_text)
            except ValueError:
                update.message.reply_text("❌ Please enter a valid number (e.g., 50, 100).")
                return ENTERING_REFERRAL_SETTINGS
                
            if threshold <= 0:
                update.message.reply_text("❌ Please enter a positive number greater than zero.")
                return ENTERING_REFERRAL_SETTINGS
                
            if threshold > 1000:
                # Confirm with the user for high values
                update.message.reply_text(
                    f"⚠️ Warning: You've set a very high threshold ({threshold} referrals).\n"
                    f"Are you sure? Please type 'confirm {threshold}' to confirm or enter a different value."
                )
                return ENTERING_REFERRAL_SETTINGS
                
            if input_text.startswith("confirm "):
                # Extract the previously entered threshold
                try:
                    threshold = int(input_text.replace("confirm ", ""))
                except ValueError:
                    update.message.reply_text("❌ Invalid confirmation format. Please try again.")
                    return ENTERING_REFERRAL_SETTINGS
            
            # Save the setting
            db.set_setting("referral_threshold", str(threshold))
            
            # Get the bonus amount to show complete info
            bonus_amount_str = db.get_setting("bonus_amount", "50.0")
            try:
                bonus_amount = float(bonus_amount_str)
            except (ValueError, TypeError):
                bonus_amount = 50.0
                logger.warning(f"Failed to convert bonus_amount to float. Using default: {bonus_amount}")
            
            # Create a keyboard to go back to referral settings
            keyboard = [
                [InlineKeyboardButton("⚙️ Back to Referral Settings", callback_data="admin_referral_settings")],
                [InlineKeyboardButton("🏠 Back to Admin Menu", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_html(
                f"✅ <b>Referral threshold updated successfully!</b>\n\n"
                f"<b>New Settings:</b>\n"
                f"• <b>Referrals Required:</b> {threshold}\n"
                f"• <b>Bonus Amount:</b> ETB {bonus_amount:.2f}\n\n"
                f"Users will now earn ETB {bonus_amount:.2f} for every {threshold} valid referrals.",
                reply_markup=reply_markup
            )
            
        elif setting_type == "bonus_amount":
            # Parse amount value
            input_text = update.message.text.strip()
            try:
                amount = float(input_text)
            except ValueError:
                update.message.reply_text("❌ Please enter a valid amount (e.g., 50.0, 100.5).")
                return ENTERING_REFERRAL_SETTINGS
                
            if amount <= 0:
                update.message.reply_text("❌ Please enter a positive amount greater than zero.")
                return ENTERING_REFERRAL_SETTINGS
                
            if amount > 1000:
                # Confirm with the user for high values
                update.message.reply_text(
                    f"⚠️ Warning: You've set a very high bonus amount (ETB {amount:.2f}).\n"
                    f"Are you sure? Please type 'confirm {amount}' to confirm or enter a different value."
                )
                return ENTERING_REFERRAL_SETTINGS
                
            if input_text.startswith("confirm "):
                # Extract the previously entered amount
                try:
                    amount = float(input_text.replace("confirm ", ""))
                except ValueError:
                    update.message.reply_text("❌ Invalid confirmation format. Please try again.")
                    return ENTERING_REFERRAL_SETTINGS
            
            # Save the setting
            db.set_setting("bonus_amount", str(amount))
            
            # Get the referral threshold to show complete info
            threshold_str = db.get_setting("referral_threshold", "50")
            try:
                threshold = int(threshold_str)
            except (ValueError, TypeError):
                threshold = 50
                logger.warning(f"Failed to convert referral_threshold to integer. Using default: {threshold}")
            
            # Create a keyboard to go back to referral settings
            keyboard = [
                [InlineKeyboardButton("⚙️ Back to Referral Settings", callback_data="admin_referral_settings")],
                [InlineKeyboardButton("🏠 Back to Admin Menu", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_html(
                f"✅ <b>Bonus amount updated successfully!</b>\n\n"
                f"<b>New Settings:</b>\n"
                f"• <b>Referrals Required:</b> {threshold}\n"
                f"• <b>Bonus Amount:</b> ETB {amount:.2f}\n\n"
                f"Users will now earn ETB {amount:.2f} for every {threshold} valid referrals.",
                reply_markup=reply_markup
            )
        
        return ADMIN_MENU
        
    except Exception as e:
        logger.error(f"Error in handle_referral_settings_input: {e}")
        update.message.reply_html(
            f"❌ An error occurred while updating the setting.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again or use /admin to return to the admin panel."
        )
        return ConversationHandler.END

def show_user_referrals(update: Update, context: CallbackContext, user_id, page=1):
    """Show referrals for a specific user with verification options"""
    # Get user data
    user_data = context.user_data.get('target_user_data') or db.get_user(user_id)
    
    # Get all referrals for this user
    all_referrals = db.get_referrals(user_id)
    
    # Filter referrals with username (real users)
    real_referrals = [ref for ref in all_referrals if ref.get('username')]
    
    # Create message
    user_display = user_data.get('username', '') or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or f"User {user_id}"
    
    message = (
        f"👥 <b>Referrals for {user_display}</b>\n\n"
        f"Total referrals: {len(all_referrals)}\n"
        f"Valid Referrals (with username): {len(real_referrals)} ✅\n"
        f"Invalid Referrals (no username): {len(all_referrals) - len(real_referrals)} ❌\n\n"
        f"<i>Note: Only referrals with usernames count toward bonuses!</i>\n\n"
    )
    
    # Pagination settings
    items_per_page = 10
    total_referrals = len(all_referrals)
    total_pages = max(1, (total_referrals + items_per_page - 1) // items_per_page)  # Ceiling division
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_referrals)
    
    # Get referrals for current page
    page_referrals = all_referrals[start_idx:end_idx]
    
    # Add referral list
    if all_referrals:
        message += f"<b>Referral List (Page {page}/{total_pages}):</b>\n"
        for i, ref in enumerate(page_referrals, start_idx + 1):
            # Format user display
            ref_username = ref.get('username', '')
            ref_name = f"{ref.get('first_name', '')} {ref.get('last_name', '')}".strip()
            ref_id = ref.get('user_id', 'Unknown')
            
            if ref_username:
                ref_display = f"@{ref_username}"
                status = "✅"  # Has username
            elif ref_name:
                ref_display = ref_name
                status = "❌"  # No username
            else:
                ref_display = f"User {ref_id}"
                status = "❌"  # No username
            
            # Format date
            created_at = ref.get('created_at', '')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        from datetime import datetime
                        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    date_str = created_at.strftime('%Y-%m-%d')
                except Exception as e:
                    date_str = str(created_at)
            else:
                date_str = "Unknown"
            
            message += f"{i}. {status} {ref_display} (ID: {ref_id}) - {date_str}\n"
        
        if total_referrals > items_per_page:
            message += f"\n<i>Showing {start_idx + 1}-{end_idx} of {total_referrals} referrals</i>"
    else:
        message += "This user has no referrals."
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"ref_admin_page_{page-1}_{user_id}")
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Next page button
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"ref_admin_page_{page+1}_{user_id}")
            )
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
    
    return ADMIN_MENU

def show_all_users(update: Update, context: CallbackContext, page=1):
    """Show list of all users with pagination"""
    query = update.callback_query
    
    # Get all users from database
    users = db.get_all_users_list(limit=1000)  # Limit to 1000 users for performance
    
    # Pagination settings
    items_per_page = 10
    total_users = len(users)
    total_pages = max(1, (total_users + items_per_page - 1) // items_per_page)  # Ceiling division
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_users)
    
    # Get users for current page
    page_users = users[start_idx:end_idx]
    
    # Format user list
    user_list = ""
    for i, user in enumerate(page_users, start_idx + 1):
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        user_id = user.get('user_id', '')
        
        # Format user display name with both username and real name if available
        user_display = ""
        if username:
            user_display += f"@{username}"
            
            # Add real name in parentheses if available
            if first_name or last_name:
                real_name = f"{first_name} {last_name}".strip()
                user_display += f" ({real_name})"
        elif first_name or last_name:
            user_display = f"{first_name} {last_name}".strip()
        else:
            user_display = "Unknown"
        
        user_list += f"{i}. {user_display} (ID: {user_id})\n"
    
    # Create message
    message = (
        f"👥 <b>All Users</b> (Total: {total_users})\n\n"
        f"<i>Showing {start_idx + 1}-{end_idx} of {total_users} users</i>\n\n"
        f"{user_list}"
    )
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_users_page_{page-1}")
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Next page button
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_users_page_{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Stats", callback_data="admin_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def show_active_users(update: Update, context: CallbackContext, page=1):
    """Show list of active users with pagination"""
    query = update.callback_query
    
    # Get active users from database
    users = db.get_active_users_list(days=7, limit=1000)  # Limit to 1000 users for performance
    
    # Pagination settings
    items_per_page = 10
    total_users = len(users)
    total_pages = max(1, (total_users + items_per_page - 1) // items_per_page)  # Ceiling division
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_users)
    
    # Get users for current page
    page_users = users[start_idx:end_idx]
    
    # Format user list
    user_list = ""
    for i, user in enumerate(page_users, start_idx + 1):
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        user_id = user.get('user_id', '')
        last_activity = user.get('last_activity', '')
        
        # Format user display name with both username and real name if available
        user_display = ""
        if username:
            user_display += f"@{username}"
            
            # Add real name in parentheses if available
            if first_name or last_name:
                real_name = f"{first_name} {last_name}".strip()
                user_display += f" ({real_name})"
        elif first_name or last_name:
            user_display = f"{first_name} {last_name}".strip()
        else:
            user_display = "Unknown"
        
        # Format last activity date
        if last_activity:
            try:
                if isinstance(last_activity, str):
                    from datetime import datetime
                    last_activity = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
                activity_str = last_activity.strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                activity_str = str(last_activity)
        else:
            activity_str = "Unknown"
        
        user_list += f"{i}. {user_display} (ID: {user_id}) - Last active: {activity_str}\n"
    
    # Create message
    message = (
        f"👤 <b>Active Users (Last 7 Days)</b> (Total: {total_users})\n\n"
        f"<i>Showing {start_idx + 1}-{end_idx} of {total_users} users</i>\n\n"
        f"{user_list}"
    )
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_active_users_page_{page-1}")
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Next page button
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_active_users_page_{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Stats", callback_data="admin_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def show_all_orders(update: Update, context: CallbackContext, page=1):
    """Show list of all orders with pagination"""
    query = update.callback_query
    
    # Get all orders from database
    orders = db.get_all_orders(limit=1000)  # Limit to 1000 orders for performance
    
    # Pagination settings
    items_per_page = 10
    total_orders = len(orders)
    total_pages = max(1, (total_orders + items_per_page - 1) // items_per_page)  # Ceiling division
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_orders)
    
    # Get orders for current page
    page_orders = orders[start_idx:end_idx]
    
    # Format order list
    order_list = ""
    for i, order in enumerate(page_orders, start_idx + 1):
        order_id = order.get('order_id', '')
        user_id = order.get('user_id', '')
        service_name = order.get('service_name', '')
        created_at = order.get('created_at', '')
        status = order.get('status', '')
        
        # Get user info
        user = db.get_user(user_id)
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        
        # Format user display with both username and real name if available
        user_display = ""
        if username:
            user_display += f"@{username}"
            
            # Add real name in parentheses if available
            if first_name or last_name:
                real_name = f"{first_name} {last_name}".strip()
                user_display += f" ({real_name})"
        elif first_name or last_name:
            user_display = f"{first_name} {last_name}".strip()
        else:
            user_display = f"User {user_id}"
        
        # Format date
        if created_at:
            try:
                if isinstance(created_at, str):
                    from datetime import datetime
                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                date_str = created_at.strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                date_str = str(created_at)
        else:
            date_str = "Unknown"
        
        # Truncate service name if too long
        if len(service_name) > 20:
            service_name = service_name[:17] + "..."
        
        order_list += f"{i}. Order #{order_id} - {service_name}\n   👤 {user_display} (ID: {user_id}) - {date_str} - Status: {status}\n\n"
    
    # Create message
    message = (
        f"📦 <b>All Orders</b> (Total: {total_orders})\n\n"
        f"<i>Showing {start_idx + 1}-{end_idx} of {total_orders} orders</i>\n\n"
        f"{order_list}"
    )
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_orders_page_{page-1}")
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Next page button
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_orders_page_{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Stats", callback_data="admin_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def show_recent_orders(update: Update, context: CallbackContext, page=1):
    """Show list of recent orders (last 7 days) with pagination"""
    query = update.callback_query
    
    # Get recent orders from database
    orders = db.get_recent_orders_list(days=7, limit=1000)  # Limit to 1000 orders for performance
    
    # Pagination settings
    items_per_page = 10
    total_orders = len(orders)
    total_pages = max(1, (total_orders + items_per_page - 1) // items_per_page)  # Ceiling division
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Calculate start and end indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_orders)
    
    # Get orders for current page
    page_orders = orders[start_idx:end_idx]
    
    # Format order list
    order_list = ""
    for i, order in enumerate(page_orders, start_idx + 1):
        order_id = order.get('order_id', '')
        user_id = order.get('user_id', '')
        service_name = order.get('service_name', '')
        created_at = order.get('created_at', '')
        status = order.get('status', '')
        
        # Get user info
        user = db.get_user(user_id)
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        
        # Format user display with both username and real name if available
        user_display = ""
        if username:
            user_display += f"@{username}"
            
            # Add real name in parentheses if available
            if first_name or last_name:
                real_name = f"{first_name} {last_name}".strip()
                user_display += f" ({real_name})"
        elif first_name or last_name:
            user_display = f"{first_name} {last_name}".strip()
        else:
            user_display = f"User {user_id}"
        
        # Format date
        if created_at:
            try:
                if isinstance(created_at, str):
                    from datetime import datetime
                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                date_str = created_at.strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                date_str = str(created_at)
        else:
            date_str = "Unknown"
        
        # Truncate service name if too long
        if len(service_name) > 20:
            service_name = service_name[:17] + "..."
        
        order_list += f"{i}. Order #{order_id} - {service_name}\n   👤 {user_display} (ID: {user_id}) - {date_str} - Status: {status}\n\n"
    
    # Create message
    message = (
        f"📦 <b>Recent Orders (Last 7 Days)</b> (Total: {total_orders})\n\n"
        f"<i>Showing {start_idx + 1}-{end_idx} of {total_orders} orders</i>\n\n"
        f"{order_list}"
    )
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        # Previous page button
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_recent_orders_page_{page-1}")
            )
        
        # Page indicator
        pagination_row.append(
            InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Next page button
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_recent_orders_page_{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Stats", callback_data="admin_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def search_user(update: Update, context: CallbackContext):
    """Search for a user by username or ID"""
    query = update.callback_query
    
    # Get search query from context
    search_query = context.user_data.get('search_query', '')
    
    # Search for users
    users = db.search_users(search_query)
    
    if not users:
        # No users found
        message = f"❌ No users found matching '{search_query}'"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    # Format user list
    user_list = ""
    for i, user in enumerate(users, 1):
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        user_id = user.get('user_id', '')
        
        # Format user display name with both username and real name if available
        user_display = ""
        if username:
            user_display += f"@{username}"
            
            # Add real name in parentheses if available
            if first_name or last_name:
                real_name = f"{first_name} {last_name}".strip()
                user_display += f" ({real_name})"
        elif first_name or last_name:
            user_display = f"{first_name} {last_name}".strip()
        else:
            user_display = "Unknown"
        
        user_list += f"{i}. {user_display} (ID: {user_id})\n"
    
    # Create message
    message = (
        f"🔍 <b>Search Results for '{search_query}'</b>\n\n"
        f"Found {len(users)} users:\n\n"
        f"{user_list}\n"
        f"Click on a user to view details and manage."
    )
    
    # Create keyboard with user buttons
    keyboard = []
    for user in users:
        user_id = user.get('user_id', '')
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        
        # Create button label
        if username:
            button_label = f"@{username}"
        elif first_name:
            button_label = first_name
        else:
            button_label = f"User {user_id}"
            
        keyboard.append([InlineKeyboardButton(button_label, callback_data=f"admin_user_{user_id}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def show_currency_rates(update: Update, context: CallbackContext):
    """Show and manage currency exchange rates"""
    query = update.callback_query
    
    # Get current currency rates
    from utils.constants import CURRENCY_RATES
    
    # Create message with current rates
    message = (
        f"💱 <b>Currency Exchange Rates</b>\n\n"
        f"Current exchange rates (1 USD to other currencies):\n\n"
    )
    
    # Add each currency rate
    for currency, rate in sorted(CURRENCY_RATES.items()):
        message += f"• <b>{currency}:</b> {rate}\n"
    
    message += "\nSelect a currency to edit its exchange rate:"
    
    # Create keyboard with currency options
    keyboard = []
    for currency in sorted(CURRENCY_RATES.keys()):
        keyboard.append([InlineKeyboardButton(f"Edit {currency} Rate", callback_data=f"admin_edit_rate_{currency}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def handle_currency_rate_input(update: Update, context: CallbackContext):
    """Process currency rate input from admin"""
    currency = context.user_data.get('edit_currency')
    
    if not currency:
        update.message.reply_text("❌ Error: Currency not specified.")
        return ConversationHandler.END
    
    try:
        # Parse rate value
        rate = float(update.message.text.strip())
        if rate <= 0:
            update.message.reply_text("❌ Please enter a positive number.")
            return ENTERING_CURRENCY_RATE
        
        # Update the rate in the database
        try:
            # Get current rate for comparison
            from utils.constants import CURRENCY_RATES
            current_rate = CURRENCY_RATES.get(currency, 0)
            
            # Update the rate in the database
            db.update_currency_rate(currency, rate)
            
            # Reload currency rates
            from utils.constants import reload_currency_rates
            reload_currency_rates()
            
            # Create keyboard to go back
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Currency Rates", callback_data="admin_currency_rates")],
                [InlineKeyboardButton("🏠 Back to Admin Menu", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Success message with comparison
            update.message.reply_html(
                f"✅ Exchange rate for <b>{currency}</b> updated successfully!\n\n"
                f"Previous rate: <b>{current_rate}</b>\n"
                f"New rate: <b>{rate}</b>\n\n"
                f"This means 1 USD = {rate} {currency}",
                reply_markup=reply_markup
            )
            
            return ADMIN_MENU
            
        except Exception as e:
            logger.error(f"Error updating currency rate: {e}")
            update.message.reply_text(
                f"❌ Failed to update currency rate: {str(e)}\n"
                f"Please try again or contact the developer."
            )
            return ENTERING_CURRENCY_RATE
        
    except ValueError:
        update.message.reply_text("❌ Please enter a valid number.")
        return ENTERING_CURRENCY_RATE

def show_service_price_options(update: Update, context: CallbackContext):
    """Show service price management options"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("🔍 Edit Single Service", callback_data="admin_edit_single_service")],
        [InlineKeyboardButton("📊 Edit Price Range", callback_data="admin_edit_price_range")],
        [InlineKeyboardButton("👀 View Price Overrides", callback_data="admin_view_price_overrides")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "🏷️ Service Price Management\n\n"
        "Select an option to manage service prices:",
        reply_markup=reply_markup
    )
    
    return ADMIN_MENU

def handle_service_id_input(update: Update, context: CallbackContext):
    """Process service ID input from admin"""
    service_id = update.message.text.strip()
    
    # Store service ID in context
    context.user_data['edit_service_id'] = service_id
    
    # Get service details from API
    from utils.api_client import api_client
    services = api_client.get_services()
    
    # Find the service with the given ID
    service = next((s for s in services if s.get('service') == service_id), None)
    
    if not service:
        update.message.reply_text(
            f"❌ Service with ID {service_id} not found.\n\n"
            f"Please enter a valid service ID or use /admin to go back to the admin panel."
        )
        return ENTERING_SERVICE_ID
    
    # Store service details in context
    context.user_data['edit_service_name'] = service.get('name', 'Unknown Service')
    context.user_data['edit_service_original_rate'] = service.get('original_rate', 0)
    context.user_data['edit_service_current_rate'] = service.get('rate', 0)
    
    # Check if service has a custom price
    has_custom_price = service.get('has_custom_price', False)
    original_rate = float(service.get('original_rate', 0))
    current_rate = float(service.get('rate', 0))
    
    # Create message
    message = (
        f"🏷️ Edit Service Price\n\n"
        f"Service ID: <code>{service_id}</code>\n"
        f"Name: {service.get('name', 'Unknown')}\n"
        f"Category: {service.get('category', 'Unknown')}\n\n"
        f"Original API Price: ${original_rate:.4f}\n"
    )
    
    if has_custom_price:
        message += f"Current Custom Price: ${current_rate:.4f}\n\n"
        message += f"This service has a custom price override.\n\n"
    else:
        message += f"Current Price (with standard markup): ${current_rate:.4f}\n\n"
    
    message += (
        f"Please enter the new absolute price for this service:\n"
        f"(This will be the exact price shown to users, no additional markup will be applied)"
    )
    
    update.message.reply_html(message)
    
    return ENTERING_SERVICE_PRICE

def handle_service_price_input(update: Update, context: CallbackContext):
    """Process service price input from admin"""
    try:
        # Parse price value
        price = float(update.message.text.strip())
        if price <= 0:
            update.message.reply_text("❌ Please enter a positive number.")
            return ENTERING_SERVICE_PRICE
        
        # Get service details from context
        service_id = context.user_data.get('edit_service_id')
        service_name = context.user_data.get('edit_service_name', 'Unknown Service')
        original_rate = context.user_data.get('edit_service_original_rate', 0)
        
        # Update the price in the database
        from utils.db import db
        success = db.set_service_price_override(
            service_id, 
            original_rate, 
            price, 
            update.effective_user.id
        )
        
        if success:
            # Invalidate any cached service data in the context
            if 'selected_service' in context.user_data:
                context.user_data.pop('selected_service', None)
            if 'order' in context.user_data and 'service_info' in context.user_data['order']:
                context.user_data['order'].pop('service_info', None)
                
            # Calculate percentage change from original price
            percentage_change = ((price - float(original_rate)) / float(original_rate)) * 100
            
            update.message.reply_html(
                f"✅ Price for service <b>{service_name}</b> (ID: <code>{service_id}</code>) "
                f"has been set to <b>${price:.4f}</b>.\n\n"
                f"This is a {percentage_change:.1f}% {'increase' if percentage_change >= 0 else 'decrease'} from the original API price (${original_rate:.4f}).\n\n"
                f"The new price is now active and will be applied to all new orders immediately.\n\n"
                f"Use /admin to return to the admin panel."
            )
        else:
            update.message.reply_text(
                f"❌ Failed to update price for service {service_name}.\n\n"
                f"Please try again or use /admin to go back to the admin panel."
            )
        
        return ConversationHandler.END
        
    except ValueError:
        update.message.reply_text("❌ Please enter a valid number.")
        return ENTERING_SERVICE_PRICE
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
        return ENTERING_SERVICE_PRICE

def show_price_range_form(update: Update, context: CallbackContext):
    """Show form for editing prices in a range"""
    query = update.callback_query
    
    query.edit_message_text(
        "📊 Edit Prices by Range\n\n"
        "This will allow you to adjust prices for all services within a specific price range.\n\n"
        "Please enter the price range and adjustment in the following format:\n"
        "<code>min_price-max_price:percentage</code>\n\n"
        "Examples:\n"
        "• <code>0-1:10</code> - Increase prices under $1 by 10%\n"
        "• <code>1-999:5</code> - Increase prices over $1 by 5%\n"
        "• <code>0-999:15</code> - Increase all prices by 15%\n"
        "• <code>0-1:-5</code> - Decrease prices under $1 by 5%\n\n"
        "Enter your price range and adjustment:",
        parse_mode="HTML"
    )
    
    return ENTERING_PRICE_RANGE

def handle_price_range_input(update: Update, context: CallbackContext):
    """Process price range input from admin"""
    input_text = update.message.text.strip()
    
    # Parse input
    try:
        range_part, percentage_part = input_text.split(':')
        min_price, max_price = map(float, range_part.split('-'))
        percentage = float(percentage_part)
        
        if min_price < 0 or max_price < 0:
            update.message.reply_text("❌ Price range cannot include negative values.")
            return ENTERING_PRICE_RANGE
        
        if min_price > max_price:
            update.message.reply_text("❌ Minimum price cannot be greater than maximum price.")
            return ENTERING_PRICE_RANGE
        
        # Get all services from API
        from utils.api_client import api_client
        services = api_client.get_services()
        
        # Filter services in the price range based on their current displayed price
        services_in_range = [
            s for s in services 
            if min_price <= float(s.get('rate', 0)) <= max_price
        ]
        
        if not services_in_range:
            update.message.reply_text(
                f"❌ No services found in the price range ${min_price:.2f} - ${max_price:.2f}."
            )
            return ENTERING_PRICE_RANGE
        
        # Calculate new prices and update in database
        from utils.db import db
        updated_count = 0
        
        for service in services_in_range:
            service_id = service.get('service')
            
            # Always use the original API price as the base for calculations
            original_rate = float(service.get('original_rate', 0))
            
            # Calculate new price directly from original rate
            # Apply the percentage change to the original price
            adjustment = original_rate * (percentage / 100)
            new_price = original_rate + adjustment
            
            # For very small percentages, ensure we're making a meaningful change
            if abs(new_price - original_rate) < 0.0001:
                new_price = original_rate * (1 + percentage/100)
            
            # Update in database
            if db.set_service_price_override(service_id, original_rate, new_price, update.effective_user.id):
                updated_count += 1
        
        # Record the bulk update
        db.update_service_prices_by_range(min_price, max_price, percentage, update.effective_user.id)
        
        # Invalidate any cached service data in the context
        if 'selected_service' in context.user_data:
            context.user_data.pop('selected_service', None)
        if 'order' in context.user_data and 'service_info' in context.user_data['order']:
            context.user_data['order'].pop('service_info', None)
        
        # Send confirmation
        update.message.reply_html(
            f"✅ Updated prices for <b>{updated_count}</b> services in the range "
            f"${min_price:.2f} - ${max_price:.2f} by {percentage}%.\n\n"
            f"The new prices are calculated based on the original API prices, not previous custom prices.\n\n"
            f"The new prices are now active and will be applied to all new orders immediately.\n\n"
            f"Use /admin to return to the admin panel."
        )
        
        return ConversationHandler.END
        
    except ValueError:
        update.message.reply_text(
            "❌ Invalid format. Please use the format: min_price-max_price:percentage\n"
            "Example: 0-1:10"
        )
        return ENTERING_PRICE_RANGE
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
        return ENTERING_PRICE_RANGE

def show_price_overrides(update: Update, context: CallbackContext):
    """Show all price overrides"""
    query = update.callback_query
    
    # Get all price overrides from database
    from utils.db import db
    overrides = db.get_all_service_price_overrides()
    
    if not overrides:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_service_prices")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            "🏷️ Price Overrides\n\n"
            "No custom price overrides found.",
            reply_markup=reply_markup
        )
        return ADMIN_MENU
    
    # Format message
    message = "🏷️ <b>Price Overrides</b>\n\n"
    
    for i, override in enumerate(overrides[:20], 1):  # Limit to 20 overrides
        service_id = override.get('service_id', 'Unknown')
        original_price = override.get('original_price', 0)
        custom_price = override.get('custom_price', 0)
        updated_at = override.get('updated_at', 'Unknown')
        
        # Format date
        if updated_at and updated_at != 'Unknown':
            try:
                if isinstance(updated_at, str):
                    from datetime import datetime
                    updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                date_str = updated_at.strftime('%Y-%m-%d %H:%M')
            except Exception:
                date_str = str(updated_at)
        else:
            date_str = "Unknown"
        
        message += (
            f"{i}. Service ID: <code>{service_id}</code>\n"
            f"   Original: ${original_price:.4f} → Custom: ${custom_price:.4f}\n"
            f"   Updated: {date_str}\n\n"
        )
    
    if len(overrides) > 20:
        message += f"<i>Showing 20 of {len(overrides)} overrides</i>\n\n"
    
    # Create keyboard with reset buttons for each override
    keyboard = []
    for override in overrides[:5]:  # Limit to 5 reset buttons
        service_id = override.get('service_id', 'Unknown')
        keyboard.append([
            InlineKeyboardButton(
                f"Reset Price for {service_id}", 
                callback_data=f"admin_reset_price_{service_id}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_service_prices")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ADMIN_MENU

def reset_service_price(update: Update, context: CallbackContext, service_id):
    """Reset price override for a service"""
    query = update.callback_query
    
    # Delete price override from database
    from utils.db import db
    success = db.delete_service_price_override(service_id)
    
    # Invalidate any cached service data in the context
    if 'selected_service' in context.user_data:
        context.user_data.pop('selected_service', None)
    if 'order' in context.user_data and 'service_info' in context.user_data['order']:
        context.user_data['order'].pop('service_info', None)
    
    if success:
        query.answer(f"Price for service {service_id} has been reset to default. The change is effective immediately.")
    else:
        query.answer(f"Failed to reset price for service {service_id}.")
    
    # Show price overrides again
    return show_price_overrides(update, context)

# Create conversation handler for admin commands
admin_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin_command)],
    states={
        ADMIN_MENU: [
            CallbackQueryHandler(admin_menu_callback, pattern=r'^admin_'),
            CallbackQueryHandler(confirm_add_balance, pattern=r'^confirm_add_balance$'),
            CallbackQueryHandler(confirm_remove_balance, pattern=r'^confirm_remove'),
            CallbackQueryHandler(handle_remove_balance_options, pattern=r'^admin_remove_'),
            CallbackQueryHandler(broadcast_confirm, pattern=r'^broadcast_confirm$|^broadcast_cancel$')
        ],
        BROADCAST_MEDIA_TYPE: [
            CallbackQueryHandler(handle_broadcast_media_type, pattern=r'^broadcast_type_')
        ],
        BROADCAST_COLLECTION: [
            CallbackQueryHandler(handle_broadcast_collection_action),
        ],
        BROADCASTING: [
            MessageHandler(Filters.text & ~Filters.command, broadcast_message),
            MessageHandler(Filters.photo, broadcast_message),
            MessageHandler(Filters.video, broadcast_message),
            MessageHandler(Filters.audio | Filters.voice, broadcast_message),
            MessageHandler(Filters.document, broadcast_message)
        ],
        VIEWING_STATS: [
            CallbackQueryHandler(admin_menu_callback, pattern=r'^admin_back$')
        ],
        ADDING_BALANCE: [
            CallbackQueryHandler(confirm_add_balance, pattern=r'^confirm_add_balance$'),
            CallbackQueryHandler(admin_menu_callback, pattern=r'^cancel_add_balance$')
        ],
        REMOVING_BALANCE_OPTIONS: [
            CallbackQueryHandler(handle_remove_balance_options, pattern=r'^admin_remove_'),
            CallbackQueryHandler(admin_menu_callback, pattern=r'^admin_back')
        ],
        ENTERING_USER_ID: [
            MessageHandler(Filters.text & ~Filters.command, handle_user_id_input)
        ],
        ENTERING_BALANCE_AMOUNT: [
            MessageHandler(Filters.text & ~Filters.command, handle_balance_amount)
        ],
        ENTERING_REFERRAL_SETTINGS: [
            MessageHandler(Filters.text & ~Filters.command, handle_referral_settings_input)
        ],
        ENTERING_CURRENCY_RATE: [
            MessageHandler(Filters.text & ~Filters.command, handle_currency_rate_input)
        ],
        ENTERING_SERVICE_ID: [
            MessageHandler(Filters.text & ~Filters.command, handle_service_id_input)
        ],
        ENTERING_SERVICE_PRICE: [
            MessageHandler(Filters.text & ~Filters.command, handle_service_price_input)
        ],
        ENTERING_PRICE_RANGE: [
            MessageHandler(Filters.text & ~Filters.command, handle_price_range_input)
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_command),
        CallbackQueryHandler(cancel_command, pattern=r'^cancel$')
    ],
    allow_reentry=True
)