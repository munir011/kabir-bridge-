import os
import sys
import logging
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)

# Import handlers
from handlers.start import start_command, language_conv_handler, referrals_command, check_referrals_callback
from handlers.services import (
    services_command, service_callback, category_callback, platform_callback,
    SELECTING_PLATFORM, SELECTING_CATEGORY, SELECTING_SERVICE, SEARCHING_SERVICES,
    process_search_term
)
from handlers.order import (
    order_command, process_link, process_quantity, process_comments, process_order, confirm_order,
    ENTERING_LINK, ENTERING_QUANTITY, ENTERING_COMMENTS, CONFIRMING_ORDER
)
from handlers.balance import balance_command, refresh_balance_callback
from handlers.admin import (
    admin_command, admin_menu_callback, broadcast_message, broadcast_confirm,
    handle_user_id_input, handle_balance_amount, confirm_add_balance, cancel_command,
    ADMIN_MENU, BROADCASTING, VIEWING_STATS, ADDING_BALANCE, ENTERING_USER_ID, ENTERING_BALANCE_AMOUNT,
    admin_conv_handler, handle_referral_settings_input, ENTERING_REFERRAL_SETTINGS
)
from handlers.help import help_command
from handlers.status import status_command, refresh_status_callback
from handlers.account import account_command, refresh_account_callback
from handlers.recharge import recharge_conv_handler, recharge_command
from handlers.support import support_command, support_conv_handler, admin_reply_conv_handler
from utils.messages import get_message
from utils.db import db

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for status conversation
STATUS_WAITING_FOR_ID = 0

def debug_callback(update, context):
    """Fallback handler for debugging"""
    query = update.callback_query
    
    if query:
        callback_data = query.data
        logger.debug(f"Received callback: {callback_data}")
        
        # Handle category callbacks that may have escaped the conversation handler
        if callback_data.startswith("cat_") or callback_data.startswith("category_"):
            logger.info(f"Handling category callback in fallback handler: {callback_data}")
            try:
                # Import required functions
                from handlers.services import category_callback, _get_services, SELECTING_SERVICE
                
                # Call the proper handler
                return category_callback(update, context)
            except Exception as e:
                logger.error(f"Error handling category in fallback: {e}", exc_info=True)
                query.answer("Error processing category")
                query.edit_message_text("There was an error processing your category selection. Please try again.")
                return
        
        # Handle platform callbacks that may have escaped
        if callback_data.startswith("plt_") or callback_data.startswith("platform_") or callback_data == "back_to_platforms":
            logger.info(f"Handling platform callback in fallback handler: {callback_data}")
            try:
                # Import required functions
                from handlers.services import platform_callback, services_command
                
                if callback_data == "back_to_platforms":
                    return services_command(update, context)
                else:
                    # Call the proper handler
                    return platform_callback(update, context)
            except Exception as e:
                logger.error(f"Error handling platform in fallback: {e}", exc_info=True)
                query.answer("Error processing platform")
                query.edit_message_text("There was an error processing your platform selection. Please try again.")
                return
        
        # Handle back to categories callback
        if callback_data == "back_to_categories":
            logger.info(f"Handling back to categories callback in fallback handler: {callback_data}")
            try:
                # Import required functions
                from handlers.services import platform_callback
                
                # Get the current platform from user data
                current_platform = context.user_data.get("current_platform", None)
                if current_platform:
                    # Create a synthetic callback with the platform ID
                    query.data = f"platform_{current_platform}"
                    return platform_callback(update, context)
                else:
                    # If no platform is stored, go back to services menu
                    from handlers.services import services_command
                    return services_command(update, context)
            except Exception as e:
                logger.error(f"Error handling back to categories: {e}", exc_info=True)
                query.answer("Error returning to categories")
                query.edit_message_text("There was an error returning to categories. Please try again.")
                return
        
        # Handle page navigation callbacks
        if callback_data.startswith("page_"):
            logger.info(f"Handling page navigation in fallback handler: {callback_data}")
            try:
                # Import required functions
                from handlers.services import service_callback
                
                # Call the service callback handler
                return service_callback(update, context)
            except Exception as e:
                logger.error(f"Error handling page navigation: {e}", exc_info=True)
                query.answer("Error navigating pages")
                query.edit_message_text("There was an error navigating between pages. Please try again.")
                return
        
        # Handle search-related callbacks
        if callback_data in ["search_services", "view_search_results"]:
            logger.info(f"Handling search callback in fallback handler: {callback_data}")
            try:
                # Import required functions
                from handlers.services import service_callback
                
                # Call the service callback handler
                return service_callback(update, context)
            except Exception as e:
                logger.error(f"Error handling search callback: {e}", exc_info=True)
                query.answer("Error with search")
                query.edit_message_text("There was an error with the search function. Please try again.")
                return
        
        # Handle confirm order button
        if callback_data == "confirm_order":
            try:
                # Get order data
                if "order" not in context.user_data:
                    query.answer("Order data not found")
                    query.edit_message_text("Error: Order data not found. Please try again.")
                    return
                
                order_data = context.user_data["order"]
                
                # Check if service_info is in order_data, if not, try to get it from selected_service
                if "service_info" not in order_data and "selected_service" in context.user_data:
                    order_data["service_info"] = context.user_data["selected_service"]["info"]
                    
                service_info = order_data.get("service_info", context.user_data.get("selected_service", {}).get("info", {}))
                service_id = order_data.get("service_id", context.user_data.get("selected_service", {}).get("id", "unknown"))
                quantity = order_data.get("quantity", 0)
                link = order_data.get("link", "No link provided")
                
                # Calculate cost - Handle string rate properly
                rate = service_info.get("rate", 0)
                try:
                    if isinstance(rate, str):
                        rate = float(rate)
                    cost = (rate / 1000) * quantity
                except (ValueError, TypeError):
                    cost = 0
                
                # Get service name for display
                service_name = service_info.get("name", "Unknown Service")
                
                # Show processing message
                query.edit_message_text(
                    f"⏳ <b>Processing Order...</b>\n\n"
                    f"Submitting order to service provider...",
                    parse_mode="HTML"
                )
                
                # Place order with API
                from utils.api_client import api_client
                
                # Log detailed order information for debugging
                logger.info(f"Placing order with API - Service ID: {service_id}, Quantity: {quantity}, Link: {link}")
                
                # Make the real API call to place the order
                response = api_client.place_order(service_id, link, quantity)
                logger.info(f"API order response: {response}")
                
                if response and isinstance(response, dict) and ('order' in response or 'id' in response):
                    # Get order ID from response
                    order_id = response.get('order', response.get('id', 'Unknown'))
                    
                    # Store order in user data for reference
                    if "orders" not in context.user_data:
                        context.user_data["orders"] = []
                        
                    context.user_data["orders"].append({
                        "order_id": order_id,
                        "service_id": service_id,
                        "service_name": service_name,
                        "link": link,
                        "quantity": quantity,
                        "cost": cost,
                        "timestamp": int(time.time())
                    })
                    
                    # Display success message
                    query.edit_message_text(
                        f"✅ <b>Order Successfully Placed!</b>\n\n"
                        f"<b>Order ID:</b> <code>{order_id}</code>\n"
                        f"<b>Service:</b> {service_name}\n"
                        f"<b>Link/Username:</b> {link}\n"
                        f"<b>Quantity:</b> {quantity}\n"
                        f"<b>Total Cost:</b> ${cost:.2f}\n\n"
                        f"You can check the status of your order with /status command.",
                        parse_mode="HTML"
                    )
                    
                    # Clear order state
                    context.user_data.pop("order_state", None)
                    return
                else:
                    error_msg = response.get("error", "Unknown error") if response else "Failed to connect to service"
                    query.edit_message_text(
                        f"❌ <b>Order Failed</b>\n\n"
                        f"There was an error placing your order: {error_msg}\n\n"
                        f"Please try again later or contact support.",
                        parse_mode="HTML"
                    )
                    
                    # Clear order state
                    context.user_data.pop("order_state", None)
                    return
            except Exception as e:
                logger.error(f"Error confirming order: {e}", exc_info=True)
                query.answer("Error confirming order")
                query.edit_message_text(f"Error confirming order: {str(e)}", parse_mode="HTML")
                return
        
        # Handle cancel order button
        if callback_data == "cancel_order":
            query.answer("Order canceled")
            query.edit_message_text("Order has been canceled.")
            # Clear order state
            context.user_data.pop("order_state", None)
            return
        
        # Handle service selection callbacks
        if callback_data.startswith("service_") or callback_data.startswith("quick_"):
            try:
                # Get service ID
                service_id = callback_data.split("_")[1]
                logger.info(f"Processing service ID: {service_id}")
                
                # Get services
                from handlers.services import _get_services
                services = _get_services()
                
                # Find service by ID
                service_info = None
                for service in services:
                    if str(service.get("service")) == service_id:
                        service_info = service
                        break
                
                if service_info:
                    # Store service info in user_data properly for both flows
                    context.user_data["selected_service"] = {
                        "id": service_id,
                        "info": service_info
                    }
                    # Also store in order for compatibility with order flow
                    if "order" not in context.user_data:
                        context.user_data["order"] = {}
                    context.user_data["order"]["service_id"] = service_id
                    context.user_data["order"]["service_info"] = service_info
                    
                    # Format service details for min/max display
                    service_name = service_info.get('name', 'Unknown Service')
                    min_quantity_display = service_info.get('min', 100)
                    max_quantity_display = service_info.get('max', 10000)
                    
                    # Convert min/max to integers for button generation
                    min_qty = min_quantity_display
                    max_qty = max_quantity_display
                    if isinstance(min_qty, str):
                        min_qty = int(min_qty)
                    if isinstance(max_qty, str):
                        max_qty = int(max_qty)

                    # Generate quantity options (starting from min, doubling until reaching max)
                    quantity_options = []
                    current_qty = min_qty
                    while current_qty <= max_qty:
                        quantity_options.append(current_qty)
                        current_qty *= 2
                        if len(quantity_options) >= 8:  # Limit to 8 buttons to avoid too many
                            break

                    # Add the max as the last option if it's not already included
                    if quantity_options[-1] < max_qty and len(quantity_options) < 8:
                        quantity_options.append(max_qty)

                    # Create quantity selection buttons
                    buttons = []
                    for i in range(0, len(quantity_options), 2):  # Create rows with 2 buttons each
                        row = []
                        row.append(InlineKeyboardButton(f"{quantity_options[i]}", callback_data=f"qty_{quantity_options[i]}"))
                        if i + 1 < len(quantity_options):
                            row.append(InlineKeyboardButton(f"{quantity_options[i+1]}", callback_data=f"qty_{quantity_options[i+1]}"))
                        buttons.append(row)

                    quantity_keyboard = InlineKeyboardMarkup(buttons)

                    # Get user language
                    user_id = query.from_user.id
                    language = db.get_language(user_id)

                    # SKIP PROCESSING MESSAGE AND ASK FOR QUANTITY DIRECTLY WITH BUTTONS
                    query.edit_message_text(
                        f"{get_message(language, 'order', 'order_quantity')}\n\n"
                        f"<b>Service:</b> {service_name}\n"
                        f"<b>Min:</b> {min_quantity_display}\n"
                        f"<b>Max:</b> {max_quantity_display}\n\n"
                        f"{get_message(language, 'order', 'please_select_quantity')}",
                        parse_mode="HTML",
                        reply_markup=quantity_keyboard
                    )
                    
                    # No need to set state for text-based quantity collection
                    # State will be handled by quantity button callback
                    return
                else:
                    query.answer("Service not found!")
                    query.edit_message_text(f"⚠️ Service with ID {service_id} not found.")
                    return
            except Exception as e:
                logger.error(f"Error in debug_callback processing service: {e}")
                query.answer("Error processing service")
                query.edit_message_text(f"Error: {str(e)}")
                return
        
        # Handle quantity buttons
        if callback_data.startswith("qty_"):
            try:
                # Extract quantity from callback data
                quantity = int(callback_data.split("_")[1])
                logger.info(f"Selected quantity: {quantity}")
                
                # Get service info
                service_info = context.user_data.get("selected_service", {}).get("info", {})
                service_name = service_info.get("name", "Unknown Service")
                
                # Save the quantity to order context
                if "order" not in context.user_data:
                    context.user_data["order"] = {}
                context.user_data["order"]["quantity"] = quantity
                
                # Store service info properly for compatibility with order handlers
                context.user_data["order"]["service_info"] = service_info
                
                # Get user language
                user_id = query.from_user.id
                language = db.get_language(user_id)
                
                # Show confirmation and ask for link/username
                query.edit_message_text(
                    get_message(language, 'order', 'quantity_set').format(quantity=quantity),
                    parse_mode="HTML"
                )
                
                # Update state to wait for link
                context.user_data["order_state"] = "waiting_for_link"
                return
            except Exception as e:
                logger.error(f"Error processing quantity selection: {e}")
                query.answer("Error processing quantity")
                query.edit_message_text("There was an error processing your quantity selection. Please try again.")
                return
        
        # Handle confirm button if not caught by conversation handler
        if callback_data == "confirm" or callback_data == "order_confirm":
            logger.info(f"Handling order confirmation in debug_callback: {callback_data}")
            try:
                from handlers.order import confirm_order
                return confirm_order(update, context)
            except Exception as e:
                logger.error(f"Error handling order confirmation: {e}", exc_info=True)
                query.answer("Error processing order")
                query.edit_message_text(
                    f"❌ <b>Order Failed</b>\n\n"
                    f"An unexpected error occurred: {str(e)}\n\n"
                    f"Please try again later or contact support.",
                    parse_mode="HTML"
                )
                return
        
        # Default handler for other callbacks - Try looking up the handler
        logger.warning(f"Unhandled callback data: {callback_data}")
        query.answer(f"Unhandled action: {callback_data}")
        return
    
    # For text messages - IMPORTANT FOR NEW FLOW
    if update.message:
        message_text = update.message.text
        logger.debug(f"Received message: {message_text}")
        
        # Handle order states for text messages
        order_state = context.user_data.get("order_state", None)
        
        # CHANGED ORDER: Handle quantity input FIRST
        if order_state == "waiting_for_quantity":
            try:
                # Parse quantity
                quantity = int(message_text.strip())
                
                # Get service info
                service_info = context.user_data.get("selected_service", {}).get("info", {})
                service_name = service_info.get("name", "Unknown Service")
                
                # ACCEPT ANY QUANTITY (Skip validation)
                
                # Save the quantity to order context
                if "order" not in context.user_data:
                    context.user_data["order"] = {}
                context.user_data["order"]["quantity"] = quantity
                
                # Store service info properly for compatibility with order handlers
                context.user_data["order"]["service_info"] = service_info
                
                # Get user language
                user_id = update.message.from_user.id
                language = db.get_language(user_id)
                
                # Show confirmation of quantity
                update.message.reply_html(
                    get_message(language, 'order', 'quantity_set').format(quantity=quantity)
                )
                
                # Update state to wait for link
                context.user_data["order_state"] = "waiting_for_link"
                return
            except ValueError:
                # Handle invalid quantity input
                update.message.reply_html(
                    "⚠️ Please enter a valid number for quantity."
                )
                return
        
        # FLOW STEP 3: Handle link input
        elif order_state == "waiting_for_link":
            # Get user input - any text is now accepted
            user_input = message_text.strip()
            
            # Save the input in the link field
            if "order" not in context.user_data:
                context.user_data["order"] = {}
            context.user_data["order"]["link"] = user_input
            
            # Get service info for confirmation
            service_info = context.user_data.get("selected_service", {}).get("info", {})
            service_name = service_info.get("name", "Unknown Service")
            
            # Make sure service_info is also in the order data
            if service_info:
                context.user_data["order"]["service_info"] = service_info
            
            quantity = context.user_data["order"].get("quantity", 0)
            
            # Calculate cost
            rate = service_info.get("rate", 0)
            try:
                if isinstance(rate, str):
                    rate = float(rate)
                cost = (rate / 1000) * quantity
            except (ValueError, TypeError):
                cost = 0
            
            # Create confirm order button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm_order")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")]
            ])
            
            # Show order summary and ask for confirmation
            update.message.reply_html(
                f"<b>Order Summary:</b>\n\n"
                f"<b>Service:</b> {service_name}\n"
                f"<b>Link/Username:</b> {user_input}\n"
                f"<b>Quantity:</b> {quantity}\n"
                f"<b>Total Cost:</b> ${cost:.2f}\n\n"
                f"<b>Confirm your order?</b>",
                reply_markup=keyboard
            )
            
            # Update state
            context.user_data["order_state"] = "confirming_order"
            return
        
        # Default handler for other messages
        update.message.reply_text(f"Received: {message_text}")
    else:
        logger.warning("Received update without message or callback query")

def handle_order_id(update: Update, context: CallbackContext):
    """Handle order ID input"""
    user = update.effective_user
    order_id = update.message.text.strip()
    
    # Import check_specific_order function and api_client
    from handlers.status import check_specific_order
    from utils.api_client import api_client
    from utils.db import db
    
    # Try to get order status from API first
    try:
        response = api_client.get_order_status(order_id)
        
        if response and not isinstance(response, list) and not response.get("error"):
            # If order exists, check the order status
            success = check_specific_order(update, context, order_id)
            if success:
                return ConversationHandler.END
        
        # If order doesn't exist or there was an error
        error_message = response.get("error", "Order not found or not accessible") if response else "Could not connect to service provider"
        
        # Get user's orders from database
        orders = db.get_user_orders(user.id, limit=20)
        
        # Create a list of order IDs if there are any orders
        order_ids_text = ""
        if orders:
            order_ids_text = "\n\n<b>Your recent order IDs:</b>\n"
            for order in orders:
                service_name = order.get('service_name', 'Unknown Service')
                # Truncate service name if too long
                if len(service_name) > 25:
                    service_name = service_name[:22] + "..."
                order_ids_text += f"<code>{order['id']}</code> - {service_name}\n"
        
        # Create keyboard with options
        keyboard = [
            [InlineKeyboardButton("📋 Show My Order IDs", callback_data="show_order_ids")],
            [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send error message with order IDs
        update.message.reply_html(
            f"⚠️ {error_message}\n\n"
            f"Please enter a valid order ID or click a button below:{order_ids_text}",
            reply_markup=reply_markup
        )
        return STATUS_WAITING_FOR_ID
    except Exception as e:
        logger.error(f"Error handling order ID: {e}")
        
        # Create keyboard with options
        keyboard = [
            [InlineKeyboardButton("📋 Show My Order IDs", callback_data="show_order_ids")],
            [InlineKeyboardButton("◀️ Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send error message
        update.message.reply_html(
            f"⚠️ An error occurred: {str(e)}\n\n"
            f"Please try again later or click a button below:",
            reply_markup=reply_markup
        )
        return STATUS_WAITING_FOR_ID

def do_nothing_callback(update: Update, context: CallbackContext):
    """Handler for do_nothing callback - just answers the callback query"""
    query = update.callback_query
    query.answer()
    return

def main():
    """Start the bot"""
    # Get the token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return
    
    logger.info(f"Starting bot with token: {token[:5]}...")
    
    # Create the Updater and pass it the bot's token
    updater = Updater(token=token, use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    
    # Add language selection handler
    dispatcher.add_handler(language_conv_handler)
    
    # Add other command handlers
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("balance", balance_command))
    dispatcher.add_handler(CommandHandler("account", account_command))
    dispatcher.add_handler(CommandHandler("support", support_command))
    
    # Add status conversation handler
    status_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("status", status_command),
            CallbackQueryHandler(status_command, pattern=r"^check_status$"),
            CallbackQueryHandler(status_command, pattern=r"^show_order_ids$")
        ],
        states={
            STATUS_WAITING_FOR_ID: [
                MessageHandler(Filters.text & ~Filters.command, handle_order_id),
                CallbackQueryHandler(status_command, pattern=r"^show_order_ids$"),
                CallbackQueryHandler(status_command, pattern=r"^check_status$"),
                CallbackQueryHandler(start_command, pattern=r"^back_to_main$")
            ]
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(start_command, pattern=r"^cancel$"),
            CallbackQueryHandler(start_command, pattern=r"^back_to_main$")
        ],
        allow_reentry=True
    )
    dispatcher.add_handler(status_conv_handler)
    
    # Add refresh status callback handler
    dispatcher.add_handler(CallbackQueryHandler(refresh_status_callback, pattern=r"^refresh_status"))
    
    # Add admin conversation handler
    dispatcher.add_handler(admin_conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(broadcast_confirm, pattern=r"^broadcast_"))
    
    # Add admin stats detail view handlers
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_view_all_users$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_view_active_users$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_view_all_orders$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_view_recent_orders$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_users_page_\d+$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_active_users_page_\d+$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_orders_page_\d+$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_recent_orders_page_\d+$"))
    
    # Add conversation handler for ordering
    order_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("services", services_command),
            CommandHandler("order", order_command),
            CallbackQueryHandler(services_command, pattern=r"^show_services$"),
            CallbackQueryHandler(order_command, pattern=r"^place_order$"),
        ],
        states={
            SELECTING_PLATFORM: [
                CallbackQueryHandler(platform_callback, pattern=r"^plt_"),
                CallbackQueryHandler(platform_callback, pattern=r"^platform_"),
                CallbackQueryHandler(start_command, pattern=r"^back_to_main$"),
                CallbackQueryHandler(service_callback, pattern=r"^search_services$")
            ],
            SELECTING_CATEGORY: [
                CallbackQueryHandler(category_callback, pattern=r"^cat_"),
                CallbackQueryHandler(category_callback, pattern=r"^category_"),
                CallbackQueryHandler(platform_callback, pattern=r"^back_to_platforms$"),
                CallbackQueryHandler(start_command, pattern=r"^back_to_main$"),
                CallbackQueryHandler(service_callback, pattern=r"^search_services$")
            ],
            SELECTING_SERVICE: [
                CallbackQueryHandler(service_callback),  # Handle all callbacks in this state
                CallbackQueryHandler(category_callback, pattern=r"^back_to_categories$"),
                CallbackQueryHandler(service_callback, pattern=r"^page_\d+$")
            ],
            SEARCHING_SERVICES: [
                MessageHandler(Filters.text & ~Filters.command, process_search_term),
                CallbackQueryHandler(category_callback, pattern=r"^back_to_categories$")
            ],
            ENTERING_LINK: [
                MessageHandler(Filters.text & ~Filters.command, process_link)
            ],
            ENTERING_QUANTITY: [
                MessageHandler(Filters.text & ~Filters.command, process_quantity)
            ],
            ENTERING_COMMENTS: [
                MessageHandler(Filters.text & ~Filters.command, process_comments)
            ],
            CONFIRMING_ORDER: [
                CallbackQueryHandler(confirm_order, pattern=r"^order_confirm$"),
                CallbackQueryHandler(confirm_order, pattern=r"^confirm$"),
                CallbackQueryHandler(lambda update, context: start_command(update, context), pattern=r"^order_cancel$"),
                CallbackQueryHandler(lambda update, context: start_command(update, context), pattern=r"^cancel$")
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(start_command, pattern=r"^cancel$")
        ],
        allow_reentry=True
    )
    dispatcher.add_handler(order_conv_handler)
    
    # Add callback query handlers for other main menu items
    dispatcher.add_handler(CallbackQueryHandler(balance_command, pattern=r"^show_balance$"))
    dispatcher.add_handler(CallbackQueryHandler(refresh_balance_callback, pattern=r"^refresh_balance$"))
    dispatcher.add_handler(CallbackQueryHandler(help_command, pattern=r"^help$"))
    dispatcher.add_handler(CallbackQueryHandler(account_command, pattern=r"^show_account$"))
    dispatcher.add_handler(CallbackQueryHandler(refresh_account_callback, pattern=r"^refresh_account$"))
    dispatcher.add_handler(CallbackQueryHandler(support_command, pattern=r"^support$"))
    
    # Add referrals command handler
    dispatcher.add_handler(CommandHandler("referrals", referrals_command))
    dispatcher.add_handler(CallbackQueryHandler(referrals_command, pattern=r"^referrals$"))
    dispatcher.add_handler(CallbackQueryHandler(check_referrals_callback, pattern=r"^check_referrals$"))
    dispatcher.add_handler(CallbackQueryHandler(check_referrals_callback, pattern=r"^ref_page_\d+$"))
    dispatcher.add_handler(CallbackQueryHandler(do_nothing_callback, pattern=r"^do_nothing$"))
    
    # Add admin referral pagination handler
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^ref_admin_page_\d+_\d+$"))
    
    # Add support conversation handlers
    dispatcher.add_handler(support_conv_handler)
    dispatcher.add_handler(admin_reply_conv_handler)
    
    # Add recharge handlers
    dispatcher.add_handler(recharge_conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(recharge_command, pattern=r"^recharge$"))
    
    # Add language change handler
    dispatcher.add_handler(CallbackQueryHandler(start_command, pattern=r"^change_language$"))
    dispatcher.add_handler(CallbackQueryHandler(start_command, pattern=r"^back_to_main$"))
    
    # Debug handler for unhandled callbacks - logs and processes them
    dispatcher.add_handler(CallbackQueryHandler(debug_callback))
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started and polling for updates")
    
    # Run the bot until you press Ctrl-C
    updater.idle()
    
    logger.info("Bot stopped")

if __name__ == "__main__":
    main() 