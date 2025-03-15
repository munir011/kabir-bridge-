from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler
from utils.db import db
from utils.messages import get_message
import logging
import os
from utils.helpers import update_user_info

# Define states
SELECTING_LANGUAGE = 0

logger = logging.getLogger(__name__)

def show_main_menu(update: Update, context: CallbackContext, language=None):
    """Helper function to show main menu"""
    user_id = update.effective_user.id
    
    if not language:
        language = db.get_language(user_id)
    
    logger.info(f"Showing main menu for user {user_id} in language: {language}")
    
    # Create main menu keyboard
    keyboard = [
        [
            InlineKeyboardButton(get_message(language, 'main_menu', 'services'), callback_data="show_services"),
            InlineKeyboardButton(get_message(language, 'main_menu', 'place_order'), callback_data="place_order")
        ],
        [
            InlineKeyboardButton(get_message(language, 'main_menu', 'balance'), callback_data="show_balance"),
            InlineKeyboardButton(get_message(language, 'main_menu', 'order_status'), callback_data="check_status")
        ],
        [
            InlineKeyboardButton(get_message(language, 'main_menu', 'recharge'), callback_data="recharge"),
            InlineKeyboardButton(get_message(language, 'main_menu', 'help'), callback_data="help")
        ],
        [
            InlineKeyboardButton(get_message(language, 'main_menu', 'referrals'), callback_data="referrals"),
            InlineKeyboardButton(get_message(language, 'main_menu', 'languages'), callback_data="change_language")
        ],
        [
            InlineKeyboardButton("💬 " + get_message(language, 'main_menu', 'support'), callback_data="support")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get welcome message
    welcome_message = get_message(language, 'welcome')
    logger.info(f"Welcome message for language {language}: {welcome_message[:30]}...")
    
    # Send welcome message
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=welcome_message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        update.message.reply_html(
            text=welcome_message,
            reply_markup=reply_markup
        )

def start_command(update: Update, context: CallbackContext):
    """Handler for /start command"""
    user = update.effective_user
    db.update_user_activity(user.id)
    
    # Update user information in the database
    update_user_info(user)
    
    # Check if this is a language change request
    if update.callback_query and update.callback_query.data == "change_language":
        current_language = db.get_language(user.id)
        
        # Create language selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 English (US)", callback_data="lang_en"),
                InlineKeyboardButton("🇬🇧 English (UK)", callback_data="lang_en_uk")
            ],
            [
                InlineKeyboardButton("🇪🇹 Amharic", callback_data="lang_am"),
                InlineKeyboardButton("🇸🇦 Arabic", callback_data="lang_ar")
            ],
            [
                InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hi"),
                InlineKeyboardButton("🇪🇸 Spanish", callback_data="lang_es")
            ],
            [
                InlineKeyboardButton("🇨🇳 Chinese", callback_data="lang_zh"),
                InlineKeyboardButton("🇹🇷 Turkish", callback_data="lang_tr")
            ],
            [
                InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send language selection message
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=get_message(current_language, 'select_language'),
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return SELECTING_LANGUAGE
    
    # Check if this is a referral link
    if update.message and context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            
            # Don't allow self-referrals
            if referrer_id != user.id:
                # Record the referral
                success = db.add_referral(referrer_id, user.id)
                
                if success:
                    # Get referrer's language
                    referrer_language = db.get_language(referrer_id)
                    
                    # Notify the referrer
                    try:
                        context.bot.send_message(
                            chat_id=referrer_id,
                            text=get_message(referrer_language, 'referrals', 'new_referral'),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Error notifying referrer {referrer_id}: {e}")
                    
                    # Get user's language
                    language = db.get_language(user.id)
                    
                    # Notify the user
                    update.message.reply_html(
                        get_message(language, 'referrals', 'welcome_referred')
                    )
                    
                    logger.info(f"User {user.id} was referred by {referrer_id}")
        except (ValueError, Exception) as e:
            logger.error(f"Error processing referral: {e}")
    
    # For normal start command, show main menu directly
    show_main_menu(update, context)
    return ConversationHandler.END

def language_callback(update: Update, context: CallbackContext):
    """Handle language selection callback"""
    query = update.callback_query
    query.answer()
    
    # Get selected language from callback data
    language = query.data.split('_')[1]
    logger.info(f"User {query.from_user.id} selected language: {language}")
    
    # Update user's language preference
    db.set_language(query.from_user.id, language)
    logger.info(f"Updated language preference for user {query.from_user.id} to {language}")
    
    # Verify the language was set correctly
    saved_language = db.get_language(query.from_user.id)
    logger.info(f"Verified language for user {query.from_user.id}: {saved_language}")
    
    # Show main menu in new language
    show_main_menu(update, context, language)
    return ConversationHandler.END

def referrals_command(update: Update, context: CallbackContext):
    """Handler for referrals command and callback"""
    user = update.effective_user
    db.update_user_activity(user.id)
    
    # Get user's language preference
    language = db.get_language(user.id)
    
    # Get bot username for creating referral link
    bot_username = context.bot.username
    
    # Create referral link
    referral_link = f"https://t.me/{bot_username}?start={user.id}"
    
    # Get referral count
    referral_count = db.get_referral_count(user.id)
    valid_referral_count = db.get_valid_referral_count(user.id)
    
    # Get referral settings
    referral_threshold = db.get_setting("referral_threshold", 50)
    
    # Check for new referral bonuses
    bonus_result = db.check_and_create_referral_bonus(user.id)
    
    # If new bonus created, notify admin
    if bonus_result:
        try:
            # Get admin chat ID
            admin_chat_id = db.get_setting("admin_chat_id")
            
            if admin_chat_id:
                # Get user info for notification
                user_info = db.get_user(user.id)
                username = user_info.get('username', '')
                first_name = user_info.get('first_name', '')
                last_name = user_info.get('last_name', '')
                
                user_display = username or f"{first_name} {last_name}".strip() or f"User {user.id}"
                
                # Send notification to admin
                context.bot.send_message(
                    chat_id=admin_chat_id,
                    text=f"🎁 <b>New Referral Bonus Request</b>\n\n"
                         f"User: {user_display} (ID: {user.id})\n"
                         f"Referrals: {bonus_result['referral_threshold']}\n"
                         f"Bonus Amount: ETB {bonus_result['bonus_amount']:.2f}\n\n"
                         f"Use /admin to approve or decline this bonus.",
                    parse_mode="HTML"
                )
                logger.info(f"Notified admin about new referral bonus for user {user.id}")
        except Exception as e:
            logger.error(f"Error notifying admin about referral bonus: {e}")
    
    # Get pending bonuses
    pending_bonuses = db.get_pending_referral_bonuses(user.id)
    
    # Get all bonuses
    all_bonuses = db.get_all_referral_bonuses(user.id)
    
    # Create bonus info text
    bonus_text = ""
    if pending_bonuses:
        bonus_text += f"<b>🕒 Pending Bonuses:</b> {len(pending_bonuses)}\n"
    
    if all_bonuses:
        approved_bonuses = [b for b in all_bonuses if b['status'] == 'approved']
        if approved_bonuses:
            total_approved = sum(b['bonus_amount'] for b in approved_bonuses)
            bonus_text += f"<b>✅ Approved Bonuses:</b> {len(approved_bonuses)} (ETB {total_approved:.2f})\n"
    
    # Add bonus info if there are any bonuses
    if bonus_text:
        bonus_amount = 50.0  # ETB 50 for each bonus
        bonus_text = (
            f"<b>🎁 Referral Bonuses:</b>\n"
            f"{bonus_text}\n"
            f"<i>You earn ETB {bonus_amount:.2f} for every {referral_threshold} valid referrals!</i>\n\n"
        )
    else:
        # Show progress towards next bonus
        remaining = referral_threshold - (valid_referral_count % referral_threshold)
        bonus_amount = 50.0  # ETB 50 for each bonus
        bonus_text = (
            f"<b>🎁 Referral Bonuses:</b>\n"
            f"<b>⏳ Progress:</b> {valid_referral_count % referral_threshold}/{referral_threshold} valid referrals\n"
            f"<b>🎯 Next Bonus:</b> {remaining} more valid referrals needed\n\n"
            f"<i>You earn ETB {bonus_amount:.2f} for every {referral_threshold} valid referrals!</i>\n\n"
        )
    
    # Create message
    message = (
        f"🔗 <b>{get_message(language, 'referrals', 'title')}</b>\n\n"
        f"{get_message(language, 'referrals', 'description')}\n\n"
        f"<b>{get_message(language, 'referrals', 'your_link')}:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"<b>{get_message(language, 'referrals', 'stats')}:</b>\n"
        f"👥 {get_message(language, 'referrals', 'total_referrals')}: <b>{referral_count}</b>\n"
        f"✅ Valid Referrals (with username): <b>{valid_referral_count}</b>\n"
        f"❌ Invalid Referrals (no username): <b>{referral_count - valid_referral_count}</b>\n\n"
        f"<i>Note: Only users with usernames count toward referral bonuses!</i>\n\n"
        f"{bonus_text}"
        f"{get_message(language, 'referrals', 'how_it_works')}"
    )
    
    # Create keyboard with share button, check referrals button, and back button
    keyboard = [
        [
            InlineKeyboardButton(get_message(language, 'referrals', 'share'), url=f"https://t.me/share/url?url={referral_link}&text={get_message(language, 'referrals', 'share_text')}")
        ],
        [
            InlineKeyboardButton("👤 " + get_message(language, 'referrals', 'check_referrals'), callback_data="check_referrals")
        ],
        [
            InlineKeyboardButton(get_message(language, 'referrals', 'back_to_menu'), callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or direct command
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        update.message.reply_html(
            message,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    return ConversationHandler.END 

def check_referrals_callback(update: Update, context: CallbackContext):
    """Handler for check referrals button"""
    query = update.callback_query
    user = update.effective_user
    db.update_user_activity(user.id)
    
    # Get user's language preference
    language = db.get_language(user.id)
    
    # Get referrals
    referrals = db.get_referrals(user.id)
    
    # Get current page from callback data or default to page 1
    callback_data = query.data
    current_page = 1
    
    # Check if this is a page navigation callback
    if callback_data.startswith("ref_page_"):
        try:
            current_page = int(callback_data.split("_")[-1])
        except (ValueError, IndexError):
            current_page = 1
    
    if not referrals:
        # No referrals yet
        message = (
            f"👥 <b>{get_message(language, 'referrals', 'check_referrals')}</b>\n\n"
            f"{get_message(language, 'referrals', 'no_referrals')}"
        )
        
        # Create back button
        keyboard = [
            [
                InlineKeyboardButton(get_message(language, 'referrals', 'back_to_referrals'), callback_data="referrals")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        # Pagination settings
        items_per_page = 25
        total_referrals = len(referrals)
        total_pages = (total_referrals + items_per_page - 1) // items_per_page  # Ceiling division
        
        # Ensure current page is valid
        if current_page < 1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages
        
        # Calculate start and end indices for the current page
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_referrals)
        
        # Get referrals for the current page
        page_referrals = referrals[start_idx:end_idx]
        
        # Count valid referrals (with username)
        valid_count = sum(1 for ref in referrals if ref.get('username'))
        
        # Format referrals list
        referrals_list = ""
        for i, referral in enumerate(page_referrals, start_idx + 1):
            # Format date
            created_at = referral.get('created_at', '')
            if created_at:
                try:
                    # Try to parse the date string
                    if isinstance(created_at, str):
                        from datetime import datetime
                        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    # Format as a readable date
                    date_str = created_at.strftime('%Y-%m-%d %H:%M')
                except Exception as e:
                    logger.error(f"Error formatting date: {e}")
                    date_str = str(created_at)
            else:
                date_str = "Unknown date"
            
            # Get user info
            username = referral.get('username', '')
            first_name = referral.get('first_name', '')
            last_name = referral.get('last_name', '')
            user_id = referral.get('user_id', 'Unknown')
            
            # Format user display name with status indicator
            if username:
                user_display = f"✅ @{username}"  # Valid referral with username
            elif first_name or last_name:
                user_display = f"❌ {first_name} {last_name}".strip()  # No username
            else:
                user_display = f"❌ User {user_id}"  # No username
            
            # Add to list
            referrals_list += f"{i}. {user_display} - {date_str}\n"
        
        # Create pagination buttons
        pagination_buttons = []
        
        # Add Previous button if not on first page
        if current_page > 1:
            pagination_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"ref_page_{current_page - 1}")
            )
        
        # Add page indicator
        pagination_buttons.append(
            InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="do_nothing")
        )
        
        # Add Next button if not on last page
        if current_page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"ref_page_{current_page + 1}")
            )
        
        # Create message with pagination info
        message = (
            f"👥 <b>{get_message(language, 'referrals', 'check_referrals')}</b>\n\n"
            f"<b>Total Referrals:</b> {total_referrals}\n"
            f"<b>Valid Referrals (with username):</b> {valid_count}\n"
            f"<b>Invalid Referrals (no username):</b> {total_referrals - valid_count}\n\n"
            f"{get_message(language, 'referrals', 'referrals_list')}:\n"
            f"<i>Showing {start_idx + 1}-{end_idx} of {total_referrals} referrals</i>\n\n"
            f"{referrals_list}"
        )
        
        # Create keyboard with pagination and back button
        keyboard = []
        
        # Add pagination row if there are multiple pages
        if total_pages > 1:
            keyboard.append(pagination_buttons)
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton(get_message(language, 'referrals', 'back_to_referrals'), callback_data="referrals")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    query.answer()
    query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return ConversationHandler.END

# Create conversation handler for language selection
language_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start_command),
        CallbackQueryHandler(start_command, pattern=r'^change_language$')
    ],
    states={
        SELECTING_LANGUAGE: [
            CallbackQueryHandler(language_callback, pattern=r'^lang_'),
            CallbackQueryHandler(start_command, pattern=r'^back_to_main$')
        ]
    },
    fallbacks=[
        CommandHandler('start', start_command),
        CallbackQueryHandler(start_command, pattern=r'^back_to_main$')
    ],
    allow_reentry=True
) 