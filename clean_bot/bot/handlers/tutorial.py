from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import logging

# Use one consistent import pattern (not both bot.utils and utils)
from utils.db import db
from utils.helpers import is_admin
from utils.messages import get_message

# Module logger
logger = logging.getLogger(__name__)

# Define states for the tutorial conversation
TUTORIAL_SELECTING_ACTION = 0
TUTORIAL_SELECTING_TUTORIAL = 1
TUTORIAL_ADDING_MEDIA = 2
TUTORIAL_SELECTING_MEDIA_TYPE = 3
TUTORIAL_ADDING_TEXT = 4

# Define tutorial types
TUTORIAL_TYPES = {
    "account": "Account Management",
    "balance": "Balance & Recharge",
    "browse": "Browse Services",
    "status": "Check Order Status",
    "support": "Contact Support",
    "referral": "Referral Program",
}

def tutorial_command(update: Update, context: CallbackContext) -> int:
    """Handler for /tutorial command - shows available tutorials"""
    user = update.effective_user
    db.update_user_activity(user.id)
    
    # Get user's language preference
    language = db.get_language(user.id)
    
    # Check if user is admin
    is_user_admin = is_admin(user.id)
    
    # Create message
    message = f"{get_message(language, 'tutorial', 'title')}\n\n"
    message += get_message(language, 'tutorial', 'select_tutorial')
    
    # Create keyboard with tutorial options
    keyboard = []
    for tutorial_id, tutorial_name in TUTORIAL_TYPES.items():
        keyboard.append([InlineKeyboardButton(tutorial_name, callback_data=f"tutorial_{tutorial_id}")])
    
    # Add admin options if user is admin
    if is_user_admin:
        keyboard.append([InlineKeyboardButton(get_message(language, 'tutorial', 'admin_manage'), callback_data="tutorial_admin")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(get_message(language, 'tutorial', 'back_to_menu'), callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both callback queries and direct messages
    if update.callback_query:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        update.message.reply_html(
            text=message,
            reply_markup=reply_markup
        )
    
    return TUTORIAL_SELECTING_TUTORIAL

def show_tutorial(update, context):
    """Show a specific tutorial to the user"""
    query = update.callback_query
    user = update.effective_user
    
    try:
        query.answer()
        
        # Get tutorial ID from callback data
        tutorial_id = query.data.split('_')[1] if len(query.data.split('_')) > 1 else None
        
        if not tutorial_id:
            query.edit_message_text("Error: Invalid tutorial selection.")
            return TUTORIAL_SELECTING_TUTORIAL
        
        # Get user language preference directly from db
        try:
            user_lang = db.get_language(user.id)
        except Exception as e:
            logging.error(f"Error getting user language: {e}")
            user_lang = 'en'  # Default to English
        
        # Get fresh tutorial content from database
        try:
            tutorial_content_obj = db.get_tutorial_content(tutorial_id)
            if tutorial_content_obj and 'text' in tutorial_content_obj:
                tutorial_content = tutorial_content_obj['text']
            else:
                tutorial_content = None
        except Exception as e:
            logging.error(f"Error fetching tutorial content: {e}")
            tutorial_content = None
        
        # Check if user is admin for showing admin options
        is_user_admin = is_admin(user.id)
        
        # Create message
        if tutorial_content:
            message = f"<b>📚 {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')}</b>\n\n"
            message += f"{tutorial_content}"
        else:
            message = f"<b>📚 {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')}</b>\n\n"
            message += "Sorry, no content is available for this tutorial yet."
        
        # Create keyboard
        keyboard = []
        
        # Add admin options if user is admin
        if is_user_admin:
            keyboard.append([
                InlineKeyboardButton("✏️ Edit", callback_data=f"tutorial_admin_edit_{tutorial_id}")
            ])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("◀️ Back", callback_data="tutorial")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to update the message
        try:
            query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Error updating tutorial message: {e}")
            # If updating fails, send a new message
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        
        # Get and send tutorial media
        try:
            tutorial_media = db.get_tutorial_media(tutorial_id)
        except Exception as e:
            logging.error(f"Error getting tutorial media: {e}")
            tutorial_media = []
        
        if tutorial_media and len(tutorial_media) > 0:
            for media in tutorial_media:
                try:
                    media_type = media['type']
                    file_id = media['file_id']
                    caption = media.get('caption', '')
                    
                    if media_type == 'photo':
                        context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'video':
                        context.bot.send_video(
                            chat_id=update.effective_chat.id,
                            video=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'document':
                        context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'voice':
                        context.bot.send_voice(
                            chat_id=update.effective_chat.id,
                            voice=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                except Exception as e:
                    logging.error(f"Error sending tutorial media: {e}")
        
        return TUTORIAL_SELECTING_TUTORIAL
    
    except Exception as e:
        logging.error(f"Error in show_tutorial: {e}")
        try:
            query.edit_message_text(
                text="An error occurred while loading the tutorial. Please try again.",
                parse_mode=ParseMode.HTML
            )
        except:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="An error occurred while loading the tutorial. Please try again.",
                parse_mode=ParseMode.HTML
            )
        return TUTORIAL_SELECTING_TUTORIAL

def admin_tutorial_menu(update: Update, context: CallbackContext) -> int:
    """Show admin tutorial management menu"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to access this menu.")
        return tutorial_command(update, context)
    
    # Get user's language preference
    language = db.get_language(user.id)
    
    # Create message
    message = "<b>🔧 Tutorial Management</b>\n\n"
    message += "Select a tutorial to edit:"
    
    # Create keyboard with tutorial options
    keyboard = []
    for tutorial_id, tutorial_name in TUTORIAL_TYPES.items():
        keyboard.append([InlineKeyboardButton(tutorial_name, callback_data=f"tutorial_admin_edit_{tutorial_id}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("◀️ Back to Tutorials", callback_data="tutorial")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return TUTORIAL_SELECTING_ACTION

def admin_edit_tutorial(update: Update, context: CallbackContext) -> int:
    """Admin interface to edit a tutorial"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to access this menu.")
        return tutorial_command(update, context)
    
    # Get tutorial ID from callback data
    tutorial_id = query.data.split('_')[3]
    
    # Store tutorial ID in context
    context.user_data['current_tutorial'] = tutorial_id
    
    # Get tutorial content from database
    tutorial_content = db.get_tutorial_content(tutorial_id)
    
    # Create message
    message = f"<b>✏️ Editing: {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')}</b>\n\n"
    
    if tutorial_content:
        message += "Current content:\n\n"
        message += tutorial_content.get('text', 'No content available.')
    else:
        message += "This tutorial doesn't have any content yet."
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Text", callback_data=f"tutorial_edit_text_{tutorial_id}"),
            InlineKeyboardButton("🖼️ Add Media", callback_data=f"tutorial_add_media_{tutorial_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Delete Media", callback_data=f"tutorial_delete_media_{tutorial_id}")
        ],
        [InlineKeyboardButton("◀️ Back to Admin Menu", callback_data="tutorial_admin")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return TUTORIAL_SELECTING_ACTION

def admin_add_media(update: Update, context: CallbackContext) -> int:
    """Admin interface to add media to a tutorial"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to access this menu.")
        return tutorial_command(update, context)
    
    # Get tutorial ID from callback data
    callback_parts = query.data.split('_')
    if len(callback_parts) >= 3 and callback_parts[1] == "add" and callback_parts[2] == "media":
        # Format: tutorial_add_media_[tutorial_id]
        tutorial_id = callback_parts[3]
    else:
        # Format: tutorial_media_[tutorial_id]
        tutorial_id = callback_parts[2]
    
    # Store tutorial ID in context
    context.user_data['current_tutorial'] = tutorial_id
    
    # Create message
    message = f"<b>🖼️ Add Media to: {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')}</b>\n\n"
    message += "Select the type of media you want to add:"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📷 Photo", callback_data=f"tutorial_media_photo_{tutorial_id}"),
            InlineKeyboardButton("🎥 Video", callback_data=f"tutorial_media_video_{tutorial_id}")
        ],
        [
            InlineKeyboardButton("📄 Document", callback_data=f"tutorial_media_document_{tutorial_id}"),
            InlineKeyboardButton("🎤 Voice", callback_data=f"tutorial_media_voice_{tutorial_id}")
        ],
        [InlineKeyboardButton("◀️ Back", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return TUTORIAL_SELECTING_MEDIA_TYPE

def admin_select_media_type(update, context):
    """Handle the selection of a media type for a tutorial"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        query.answer("You are not authorized to perform this action.")
        return TUTORIAL_SELECTING_ACTION
    
    try:
        query.answer()
        
        # Handle both simple and complex media callback patterns
        callback_data = query.data
        logging.info(f"Processing media type selection callback: {callback_data}")
        
        # Parse callback data which might be in format:
        # 'tutorial_media_photo' or 'tutorial_media_photo_video' or similar
        parts = callback_data.split('_')
        
        # Determine media type and tutorial ID
        media_type = None
        tutorial_id = None
        
        if len(parts) >= 3:
            # Extract tutorial ID from context if available
            if 'current_tutorial' in context.user_data:
                tutorial_id = context.user_data['current_tutorial']
            
            # For simple format like 'tutorial_media_photo'
            if len(parts) == 3:
                media_type = parts[2]
            
            # For complex format like 'tutorial_media_photo_video'
            # In this case, 'photo' is the media_type and 'video' is the tutorial_id
            elif len(parts) == 4:
                media_type = parts[2]
                tutorial_id = parts[3]
        
        # Validate media type
        valid_media_types = ['photo', 'video', 'document', 'voice']
        if media_type not in valid_media_types:
            query.edit_message_text(
                text=f"Invalid media type: {media_type}. Please select a valid type.",
                parse_mode=ParseMode.HTML
            )
            return TUTORIAL_SELECTING_ACTION
        
        if not tutorial_id:
            query.edit_message_text(
                text="Error: Could not determine tutorial ID. Please try again.",
                parse_mode=ParseMode.HTML
            )
            return TUTORIAL_SELECTING_ACTION
        
        # Store the tutorial ID and media type in context (all naming conventions for compatibility)
        context.user_data['current_tutorial_id'] = tutorial_id
        context.user_data['current_tutorial'] = tutorial_id
        context.user_data['current_media_type'] = media_type
        context.user_data['media_type'] = media_type
        
        logging.info(f"Set context variables: tutorial_id={tutorial_id}, media_type={media_type}")
        
        # Create keyboard for cancel option
        keyboard = [
            [InlineKeyboardButton("Cancel", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Message to prompt user to send media
        message = f"Please send me a {media_type} to add to the tutorial."
        
        try:
            # Try to edit the message
            query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            # If editing fails (e.g., media message can't be edited to text),
            # send a new message
            logging.error(f"Error updating message: {e}")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        
        return TUTORIAL_ADDING_MEDIA
    
    except Exception as e:
        logging.error(f"Error in admin_select_media_type: {e}")
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"An error occurred: {str(e)}. Please try again.",
            parse_mode=ParseMode.HTML
        )
        return TUTORIAL_SELECTING_ACTION

def admin_receive_media(update: Update, context: CallbackContext) -> int:
    """Handle receiving media from admin"""
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        update.message.reply_text("You don't have permission to add media to tutorials.")
        return ConversationHandler.END
    
    # Get tutorial ID and media type from context (check both naming conventions)
    tutorial_id = context.user_data.get('current_tutorial')
    media_type = context.user_data.get('current_media_type')  # First try the new key
    
    if not media_type:
        media_type = context.user_data.get('media_type')  # Fallback to old key
        
    logging.info(f"Receiving media for tutorial {tutorial_id}, media type: {media_type}")
    
    if not tutorial_id or not media_type:
        error_msg = f"Error: Tutorial info missing. tutorial_id: {tutorial_id}, media_type: {media_type}"
        logging.error(error_msg)
        update.message.reply_text(error_msg)
        return TUTORIAL_SELECTING_ACTION
    
    # Get file ID and caption based on media type
    file_id = None
    caption = ""
    
    try:
        if media_type == 'photo' and update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            logging.info(f"Received photo with file_id: {file_id[:20]}...")
        elif media_type == 'video' and update.message.video:
            file_id = update.message.video.file_id
            caption = update.message.caption or ""
            logging.info(f"Received video with file_id: {file_id[:20]}...")
        elif media_type == 'document' and update.message.document:
            file_id = update.message.document.file_id
            caption = update.message.caption or ""
            logging.info(f"Received document with file_id: {file_id[:20]}...")
        elif media_type == 'voice' and update.message.voice:
            file_id = update.message.voice.file_id
            caption = update.message.caption or ""
            logging.info(f"Received voice with file_id: {file_id[:20]}...")
        else:
            logging.warning(f"Received incorrect media type. Expected {media_type}, got: {update.message}")
    except Exception as e:
        logging.error(f"Error extracting file_id: {e}")
    
    if file_id:
        # CHANGED: Instead of saving to database immediately, store in context and ask for confirmation
        # Store the media info in user_data for later use
        context.user_data['pending_media'] = {
            'tutorial_id': tutorial_id,
            'media_type': media_type,
            'file_id': file_id,
            'caption': caption
        }
        
        # Show preview of the media and ask for confirmation
        message = f"✅ {media_type.capitalize()} received. Would you like to publish it to the {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')} tutorial?"
        
        # Send the media as a preview
        if media_type == 'photo':
            update.message.reply_photo(
                photo=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        elif media_type == 'video':
            update.message.reply_video(
                video=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        elif media_type == 'document':
            update.message.reply_document(
                document=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        elif media_type == 'voice':
            update.message.reply_voice(
                voice=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        
        # Create keyboard with Publish and Cancel buttons
        keyboard = [
            [InlineKeyboardButton("✅ Publish", callback_data=f"tutorial_publish_media_{tutorial_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"tutorial_admin_edit_{tutorial_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Ask for confirmation
        update.message.reply_html(
            text=message,
            reply_markup=reply_markup
        )
        
        return TUTORIAL_SELECTING_ACTION  # Return to action selection to handle the publish callback
    else:
        # Wrong media type was sent
        message = f"❌ Error: Please send a {media_type}. The message you sent doesn't contain the expected media type."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data=f"tutorial_media_{media_type}_{tutorial_id}")],
            [InlineKeyboardButton("◀️ Back to Tutorial", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_html(
            text=message,
            reply_markup=reply_markup
        )
        
        return TUTORIAL_SELECTING_MEDIA_TYPE

def admin_publish_media(update: Update, context: CallbackContext) -> int:
    """Handle publishing media to a tutorial after confirmation"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to publish media to tutorials.")
        return tutorial_command(update, context)
    
    query.answer("Publishing media...")
    
    # Get the pending media information from context
    pending_media = context.user_data.get('pending_media', {})
    logging.info(f"Publishing media with data: {pending_media}")
    
    if not pending_media:
        query.edit_message_text("Error: No pending media to publish.")
        return TUTORIAL_SELECTING_ACTION
    
    tutorial_id = pending_media.get('tutorial_id')
    media_type = pending_media.get('media_type')
    file_id = pending_media.get('file_id')
    caption = pending_media.get('caption', '')
    
    logging.info(f"Publishing {media_type} to tutorial {tutorial_id} with file_id: {file_id}")
    
    # Save media to database - using try/except with detailed error logging
    success = False
    try:
        # Add the media to the tutorial in the database
        success = db.add_tutorial_media(tutorial_id, media_type, file_id, caption)
        if success:
            logging.info(f"Successfully published {media_type} to tutorial {tutorial_id}")
        else:
            logging.error(f"Database returned False when adding media to tutorial {tutorial_id}")
    except Exception as e:
        logging.error(f"Error saving media to database: {e}", exc_info=True)
        query.edit_message_text(
            f"❌ Error publishing media: {str(e)}"
        )
        return TUTORIAL_SELECTING_ACTION
    
    if not success:
        query.edit_message_text(
            "❌ Error publishing media: Database operation failed."
        )
        return TUTORIAL_SELECTING_ACTION
    
    # Clear pending media from context
    context.user_data.pop('pending_media', None)
    
    # Confirm to admin
    message = f"✅ {media_type.capitalize()} has been published to the {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')} tutorial."
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("➕ Add Another Media", callback_data=f"tutorial_add_media_{tutorial_id}")],
        [InlineKeyboardButton("◀️ Back to Tutorial", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Error updating confirmation message: {e}", exc_info=True)
        # If editing fails, send a new message
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    # Show updated tutorial content with all media
    try:
        # Get fresh data from the database
        tutorial_content = db.get_tutorial_content(tutorial_id)
        logging.info(f"Retrieved tutorial content: {tutorial_content}")
        media_files = db.get_tutorial_media(tutorial_id)
        logging.info(f"Retrieved {len(media_files)} media files")
        
        # First show the tutorial text
        preview = f"<b>📚 Preview of {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')} with media:</b>\n\n"
        
        if tutorial_content and 'text' in tutorial_content:
            preview += tutorial_content.get('text')
        else:
            preview += "No content available."
        
        # Send the tutorial text as a separate message
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=preview,
            parse_mode=ParseMode.HTML
        )
        
        # Now show all media files - if there are any
        if media_files and len(media_files) > 0:
            # First send a header message
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>📎 All tutorial media:</b>",
                parse_mode=ParseMode.HTML
            )
            
            # Then send each media file
            for i, media in enumerate(media_files):
                try:
                    media_type = media.get('type')
                    file_id = media.get('file_id')
                    caption = media.get('caption', '')
                    
                    logging.info(f"Sending media {i+1}/{len(media_files)}: type={media_type}, file_id={file_id[:15]}...")
                    
                    if media_type == 'photo':
                        context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'video':
                        context.bot.send_video(
                            chat_id=update.effective_chat.id,
                            video=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'document':
                        context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif media_type == 'voice':
                        context.bot.send_voice(
                            chat_id=update.effective_chat.id,
                            voice=file_id,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    logging.info(f"Successfully sent media {i+1}")
                except Exception as e:
                    logging.error(f"Error sending media {i+1}: {e}", exc_info=True)
                    # If sending a specific media fails, send a text message with the error
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"❌ Error sending {media_type} #{i+1}: {str(e)}",
                        parse_mode=ParseMode.HTML
                    )
        else:
            # If no media files were found, send a message
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>⚠️ No media files found for this tutorial.</b>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logging.error(f"Error showing media preview: {e}", exc_info=True)
        # If there's an error with the preview, inform the user
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Error showing preview: {str(e)}",
            parse_mode=ParseMode.HTML
        )
    
    return TUTORIAL_SELECTING_ACTION

def admin_delete_media(update: Update, context: CallbackContext) -> int:
    """Admin interface to delete media from a tutorial"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to access this menu.")
        return tutorial_command(update, context)
    
    # Get tutorial ID from callback data
    tutorial_id = query.data.split('_')[3]
    
    # Get media files for this tutorial
    media_files = db.get_tutorial_media(tutorial_id)
    
    if not media_files:
        query.answer("This tutorial doesn't have any media files.")
        return admin_edit_tutorial(update, context)
    
    # Create message
    message = f"<b>🗑️ Delete Media from: {TUTORIAL_TYPES.get(tutorial_id, 'Tutorial')}</b>\n\n"
    message += "Select the media file you want to delete:"
    
    # Create keyboard
    keyboard = []
    
    for i, media in enumerate(media_files):
        media_type = media.get('type', 'unknown').capitalize()
        caption = media.get('caption', 'No caption')
        
        # Truncate caption if too long
        if len(caption) > 30:
            caption = caption[:27] + "..."
        
        keyboard.append([
            InlineKeyboardButton(f"{i+1}. {media_type}: {caption}", callback_data=f"tutorial_delete_media_item_{tutorial_id}_{i}")
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data=f"tutorial_admin_edit_{tutorial_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return TUTORIAL_SELECTING_ACTION

def admin_delete_media_item(update: Update, context: CallbackContext) -> int:
    """Delete a specific media item from a tutorial"""
    query = update.callback_query
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        query.answer("You don't have permission to access this menu.")
        return tutorial_command(update, context)
    
    # Get tutorial ID and media index from callback data
    parts = query.data.split('_')
    tutorial_id = parts[4]
    media_index = int(parts[5])
    
    # Delete the media from database
    success = db.delete_tutorial_media(tutorial_id, media_index)
    
    if success:
        query.answer("Media has been deleted successfully.")
    else:
        query.answer("Error: Could not delete the media.")
    
    # Return to the tutorial edit menu
    return admin_edit_tutorial(update, context)

def admin_edit_text(update, context):
    """Handle admin editing tutorial text"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        query.answer("You are not authorized to perform this action.")
        return TUTORIAL_SELECTING_ACTION
    
    try:
        query.answer()
        
        # Get tutorial ID from callback data (either tutorial_edit_text_ID or tutorial_edit_ID)
        callback_data = query.data
        parts = callback_data.split('_')
        
        tutorial_id = None
        if len(parts) >= 3:
            if parts[1] == "edit" and parts[2] == "text":  # tutorial_edit_text_ID
                tutorial_id = parts[3] if len(parts) > 3 else None
            elif parts[1] == "edit":  # tutorial_edit_ID
                tutorial_id = parts[2]
        
        if not tutorial_id:
            query.edit_message_text(
                text="Error: Invalid tutorial selection.",
                parse_mode=ParseMode.HTML
            )
            return TUTORIAL_SELECTING_ACTION
        
        # Store tutorial ID in context for handle_tutorial_text (both keys for compatibility)
        context.user_data['editing_tutorial_id'] = tutorial_id
        context.user_data['current_tutorial'] = tutorial_id
        
        # Log what we're doing
        logging.info(f"Preparing to edit tutorial: {tutorial_id}")
        
        # Get current tutorial content for reference (direct DB call)
        try:
            tutorial_content_obj = db.get_tutorial_content(tutorial_id)
            if tutorial_content_obj and 'text' in tutorial_content_obj:
                tutorial_content = tutorial_content_obj['text']
            else:
                tutorial_content = None
        except Exception as e:
            logging.error(f"Error fetching tutorial content: {e}")
            tutorial_content = None
            
        tutorial_type = TUTORIAL_TYPES.get(tutorial_id, "Unknown")
        
        # Prepare message asking for new text
        message = f"<b>✏️ Edit {tutorial_type} Tutorial</b>\n\n"
        message += "Please send me the new text for this tutorial. You can use HTML formatting.\n\n"
        message += "<b>Current content:</b>\n"
        message += f"{tutorial_content}" if tutorial_content else "No content available."
        
        # Create keyboard with cancel option
        keyboard = [
            [InlineKeyboardButton("Cancel", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to edit the message
        try:
            query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Error updating message in admin_edit_text: {e}")
            # If editing fails, send a new message
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        
        return TUTORIAL_ADDING_TEXT
    
    except Exception as e:
        logging.error(f"Error in admin_edit_text: {e}")
        query.edit_message_text(
            text=f"An error occurred: {str(e)}. Please try again.",
            parse_mode=ParseMode.HTML
        )
        return TUTORIAL_SELECTING_ACTION

def handle_tutorial_text(update: Update, context: CallbackContext) -> int:
    """Handle the text input for a tutorial"""
    user = update.effective_user
    
    # Verify user is admin
    if not is_admin(user.id):
        update.message.reply_text("You don't have permission to edit tutorials.")
        return TUTORIAL_SELECTING_ACTION
    
    # Get user input
    new_text = update.message.text
    
    # Get tutorial ID from context
    tutorial_id = context.user_data.get('editing_tutorial_id')
    if not tutorial_id:
        # Try the older key as fallback
        tutorial_id = context.user_data.get('current_tutorial')
        
    if not tutorial_id:
        update.message.reply_text("Error: No tutorial selected for editing.")
        return TUTORIAL_SELECTING_ACTION
    
    # Validate input - ensure it's not just a language code or too short
    if len(new_text) <= 3 or new_text.lower() in ['en', 'am']:
        update.message.reply_text(
            "The tutorial text is too short or appears to be just a language code. "
            "Please provide detailed tutorial content."
        )
        return TUTORIAL_ADDING_TEXT
    
    # Update tutorial in database - using direct db call
    success = False
    try:
        db.update_tutorial_text(tutorial_id, new_text)
        success = True
        logging.info(f"Updated tutorial {tutorial_id} with text: {new_text[:30]}...")
    except Exception as e:
        logging.error(f"Error in handle_tutorial_text: {e}")
        success = False
    
    if success:
        # Get the updated tutorial to show a preview
        try:
            # Get fresh content directly from db
            tutorial_content = db.get_tutorial_content(tutorial_id)
            if tutorial_content and 'text' in tutorial_content:
                tutorial_text = tutorial_content['text']
            else:
                tutorial_text = new_text  # Use the input text as fallback
                
            # Get media files
            tutorial_media = db.get_tutorial_media(tutorial_id)
            
            # Get tutorial type name
            tutorial_type = TUTORIAL_TYPES.get(tutorial_id, "Unknown")
            
            # Confirm the text was saved
            update.message.reply_html(
                f"✅ Tutorial text for <b>{tutorial_type}</b> has been updated successfully."
            )
            
            # Show preview of the updated tutorial content
            preview_message = f"<b>🔍 Preview of {tutorial_type} Tutorial:</b>\n\n"
            preview_message += f"{tutorial_text}\n\n"
            
            # Add info about media if any
            if tutorial_media and len(tutorial_media) > 0:
                preview_message += f"<b>📎 This tutorial has {len(tutorial_media)} media items attached.</b>"
            
            # Create keyboard to return to admin menu
            keyboard = [
                [InlineKeyboardButton("Back to Admin Menu", callback_data=f"tutorial_admin_edit_{tutorial_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send preview message
            try:
                update.message.reply_html(
                    text=preview_message,
                    reply_markup=reply_markup
                )
                
                # If there are media files, send them as separate messages
                if tutorial_media and len(tutorial_media) > 0:
                    for media in tutorial_media:
                        try:
                            media_type = media['type']
                            file_id = media['file_id']
                            caption = media.get('caption', '')
                            
                            if media_type == 'photo':
                                update.message.reply_photo(
                                    photo=file_id,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                            elif media_type == 'video':
                                update.message.reply_video(
                                    video=file_id,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                            elif media_type == 'document':
                                update.message.reply_document(
                                    document=file_id,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                            elif media_type == 'voice':
                                update.message.reply_voice(
                                    voice=file_id,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                        except Exception as e:
                            logging.error(f"Error sending media preview: {e}")
            except Exception as e:
                logging.error(f"Error sending preview message: {e}")
                update.message.reply_html(
                    "Error sending preview. The tutorial has been updated successfully."
                )
        except Exception as e:
            logging.error(f"Error getting preview content: {e}")
            update.message.reply_html(
                f"✅ Tutorial text has been updated successfully, but there was an error showing the preview."
            )
    else:
        update.message.reply_html(
            "❌ Failed to update the tutorial. Please try again."
        )
    
    return TUTORIAL_SELECTING_ACTION

def tutorial_conversation_handler():
    """Create a conversation handler for the tutorial system"""
    return ConversationHandler(
        entry_points=[
            CommandHandler('tutorial', tutorial_command),
            CallbackQueryHandler(tutorial_command, pattern='^tutorial$'),
        ],
        states={
            TUTORIAL_SELECTING_TUTORIAL: [
                CallbackQueryHandler(show_tutorial, pattern='^tutorial_[a-z]+$'),
                CallbackQueryHandler(admin_tutorial_menu, pattern='^tutorial_admin$'),
                CallbackQueryHandler(tutorial_command, pattern='^tutorial$'),
            ],
            TUTORIAL_SELECTING_ACTION: [
                CallbackQueryHandler(admin_edit_tutorial, pattern='^tutorial_admin_edit_[a-z]+$'),
                CallbackQueryHandler(admin_add_media, pattern='^tutorial_add_media_[a-z]+$'),
                CallbackQueryHandler(admin_delete_media, pattern='^tutorial_delete_media_[a-z]+$'),
                CallbackQueryHandler(admin_delete_media_item, pattern='^tutorial_delete_media_item_[a-z]+_[0-9]+$'),
                CallbackQueryHandler(admin_edit_text, pattern='^tutorial_edit_text_[a-z]+$'),
                CallbackQueryHandler(admin_edit_text, pattern='^tutorial_edit_[a-z]+$'),
                CallbackQueryHandler(admin_add_media, pattern='^tutorial_media_[a-z]+$'),
                CallbackQueryHandler(admin_publish_media, pattern='^tutorial_publish_media_[a-z]+$'),  # Add new callback
            ],
            TUTORIAL_SELECTING_MEDIA_TYPE: [
                CallbackQueryHandler(admin_select_media_type, pattern='^tutorial_media_[a-z]+_[a-z]+$'),
                CallbackQueryHandler(admin_select_media_type, pattern='^tutorial_media_'),
            ],
            TUTORIAL_ADDING_MEDIA: [
                MessageHandler(Filters.photo | Filters.video | Filters.document | Filters.voice, admin_receive_media),
            ],
            TUTORIAL_ADDING_TEXT: [
                MessageHandler(Filters.text & ~Filters.command, handle_tutorial_text),
                CallbackQueryHandler(admin_edit_tutorial, pattern='^tutorial_admin_edit_[a-z]+$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(tutorial_command, pattern='^tutorial$'),
            CallbackQueryHandler(lambda u, c: -1, pattern='^back_to_main$'),
        ],
        map_to_parent={
            -1: ConversationHandler.END,
        },
        allow_reentry=True,
        name="tutorial_conversation",
    )

# Handler for tutorial text input (outside the conversation handler)
def tutorial_text_handler(update: Update, context: CallbackContext) -> None:
    """Handle text input for tutorial editing"""
    if context.user_data.get('awaiting_tutorial_text'):
        handle_tutorial_text(update, context)

def get_tutorial_content(tutorial_id):
    """Get tutorial content from database"""
    try:
        # Import db here to avoid circular imports
        from utils.db import get_tutorial_content as db_get_tutorial_content
        content = db_get_tutorial_content(tutorial_id)
        if content and 'text' in content:
            return content['text']
        return None
    except Exception as e:
        logging.error(f"Error getting tutorial content: {e}")
        return None

def get_tutorial_media(tutorial_id):
    """Get tutorial media from database"""
    try:
        # Import db here to avoid circular imports
        from utils.db import get_tutorial_media as db_get_tutorial_media
        return db_get_tutorial_media(tutorial_id)
    except Exception as e:
        logging.error(f"Error getting tutorial media: {e}")
        return []

def get_user_language(user_id):
    """Get user language preference"""
    try:
        # Import db here to avoid circular imports
        from utils.db import get_language
        return get_language(user_id)
    except Exception as e:
        logging.error(f"Error getting user language: {e}")
        return 'en'  # Default to English