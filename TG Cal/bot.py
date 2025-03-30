from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import logging
import re

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store user-specific settings
user_settings = {}

# Function to calculate lot size
def calculate_lot_size(balance, risk_percent, stop_loss_pips=50, pip_value=10.0):
    risk_amount = balance * (risk_percent / 100)
    lot_size = risk_amount / (stop_loss_pips * pip_value)
    return round(lot_size, 2)

# Helper function to generate a professional response
def generate_lot_response(balance, risk_percent, stop_loss_pips=50):
    lot_size = calculate_lot_size(balance, risk_percent, stop_loss_pips)
    
    # Calculate additional information
    risk_amount = balance * (risk_percent / 100)
    pip_value = 10.0  # You can adjust this based on the currency pair
    
    response = (
        f"*📊 Risk Management Analysis*\n\n"
        f"💵 *Account Balance:* ${balance:,.2f}\n"
        f"⚠️ *Risk Percentage:* {risk_percent}%\n"
        f"🛑 *Stop Loss:* {stop_loss_pips} pips\n\n"
        f"💰 *Risk Amount:* ${risk_amount:,.2f}\n"
        f"🎯 *Recommended Lot Size:* {lot_size} lots\n\n"
        f"_Remember: Never risk more than you can afford to lose._"
    )
    return response

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    
    # Add user to settings if not exists
    user_id = update.effective_chat.id
    if user_id not in user_settings:
        user_settings[user_id] = {
            "risk_percent": 2,
            "stop_loss_pips": 50
        }
    
    keyboard = [
        [InlineKeyboardButton("Set Risk %", callback_data="set_risk"),
         InlineKeyboardButton("Set Stop Loss", callback_data="set_sl")],
        [InlineKeyboardButton("Calculate Lot Size", callback_data="calc_lot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"*Welcome to the Pro Risk Management Bot!* 🤖\n\n"
        f"Hello {user.first_name}! I'll help you manage your trading risk professionally.\n\n"
        f"*Current Settings:*\n"
        f"• Risk: {user_settings[user_id]['risk_percent']}%\n"
        f"• Stop Loss: {user_settings[user_id]['stop_loss_pips']} pips\n\n"
        f"*Commands:*\n"
        f"• Send any number to calculate lot size\n"
        f"• /setrisk <percentage> - Set risk percentage\n"
        f"• /setsl <pips> - Set stop loss in pips\n"
        f"• /settings - View your current settings\n"
        f"• /help - Show detailed instructions\n\n"
        f"_Trade smart, manage risk!_ 📈",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a detailed help message when the command /help is issued."""
    await update.message.reply_text(
        "*📚 Pro Risk Management Bot - Help Guide*\n\n"
        "*Basic Commands:*\n"
        "• /start - Initialize the bot and see welcome screen\n"
        "• /help - Display this help information\n"
        "• /settings - View your current risk settings\n\n"
        
        "*Risk Management:*\n"
        "• /setrisk <percentage> - Set your risk percentage (e.g., /setrisk 2.5)\n"
        "• /setsl <pips> - Set your default stop loss in pips (e.g., /setsl 45)\n\n"
        
        "*Calculations:*\n"
        "• Simply send your account balance (e.g., 1000) to get lot size recommendations\n"
        "• For advanced calculation: /calculate <balance> <risk%> <stop_loss>\n\n"
        
        "*Using in a Channel:*\n"
        "• Admins can add this bot to a channel\n"
        "• Use the format @YourBotName 1000 to calculate lot size in a channel\n"
        "• Or tag the bot: @YourBotName /calculate 1000 2 50\n\n"
        
        "_Need more help? Contact the developer._",
        parse_mode=ParseMode.MARKDOWN
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current user settings."""
    user_id = update.effective_chat.id
    
    # Initialize settings if not exists
    if user_id not in user_settings:
        user_settings[user_id] = {
            "risk_percent": 2,
            "stop_loss_pips": 50
        }
    
    settings = user_settings[user_id]
    
    keyboard = [
        [InlineKeyboardButton("Change Risk %", callback_data="set_risk"),
         InlineKeyboardButton("Change Stop Loss", callback_data="set_sl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"*⚙️ Your Current Settings*\n\n"
        f"🔹 *Risk Percentage:* {settings['risk_percent']}%\n"
        f"🔹 *Stop Loss:* {settings['stop_loss_pips']} pips\n\n"
        f"*Examples with these settings:*\n"
        f"- A $1,000 account would risk ${1000 * settings['risk_percent']/100:.2f}\n"
        f"- Recommended lot size would be {calculate_lot_size(1000, settings['risk_percent'], settings['stop_loss_pips'])} lots\n\n"
        f"_Click below to adjust your settings:_",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def set_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set custom risk percentage."""
    try:
        # Get the custom risk percentage
        risk_percent = float(context.args[0])
        
        # Validate risk percentage
        if risk_percent <= 0 or risk_percent > 10:
            await update.message.reply_text(
                "⚠️ *Risk Warning*\n\n"
                "Risk percentage must be between 0.1 and 10%.\n"
                "Setting risk too high can lead to significant losses.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store the user's custom risk percentage
        user_id = update.effective_chat.id
        if user_id not in user_settings:
            user_settings[user_id] = {"risk_percent": risk_percent, "stop_loss_pips": 50}
        else:
            user_settings[user_id]["risk_percent"] = risk_percent
        
        # Confirm the update
        await update.message.reply_text(
            f"✅ *Risk Updated Successfully*\n\n"
            f"Your risk percentage is now set to *{risk_percent}%*.\n\n"
            f"_Send your account balance to calculate your lot size with the new risk setting._",
            parse_mode=ParseMode.MARKDOWN
        )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ *Invalid Input*\n\n"
            "Usage: /setrisk <percentage>\n"
            "Example: /setrisk 2.5\n\n"
            "_This would set your risk to 2.5% of your account balance per trade._",
            parse_mode=ParseMode.MARKDOWN
        )

async def set_stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set custom stop loss in pips."""
    try:
        # Get the custom stop loss
        stop_loss = int(context.args[0])
        
        # Validate stop loss
        if stop_loss <= 0 or stop_loss > 1000:
            await update.message.reply_text(
                "⚠️ *Input Error*\n\n"
                "Stop loss must be between 1 and 1000 pips.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store the user's custom stop loss
        user_id = update.effective_chat.id
        if user_id not in user_settings:
            user_settings[user_id] = {"risk_percent": 2, "stop_loss_pips": stop_loss}
        else:
            user_settings[user_id]["stop_loss_pips"] = stop_loss
        
        # Confirm the update
        await update.message.reply_text(
            f"✅ *Stop Loss Updated*\n\n"
            f"Your default stop loss is now set to *{stop_loss} pips*.\n\n"
            f"_This will be used for all lot size calculations unless overridden._",
            parse_mode=ParseMode.MARKDOWN
        )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "❌ *Invalid Input*\n\n"
            "Usage: /setsl <pips>\n"
            "Example: /setsl 50\n\n"
            "_This would set your default stop loss to 50 pips._",
            parse_mode=ParseMode.MARKDOWN
        )

async def advanced_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle advanced calculation with parameters."""
    try:
        # Require at least balance
        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ *Missing Parameters*\n\n"
                "Usage: /calculate <balance> [risk%] [stop_loss]\n"
                "Example: /calculate 1000 2 50",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        # Get parameters
        balance = float(context.args[0])
        
        user_id = update.effective_chat.id
        if user_id not in user_settings:
            user_settings[user_id] = {"risk_percent": 2, "stop_loss_pips": 50}
            
        # Get optional parameters
        risk_percent = float(context.args[1]) if len(context.args) > 1 else user_settings[user_id]["risk_percent"]
        stop_loss = int(context.args[2]) if len(context.args) > 2 else user_settings[user_id]["stop_loss_pips"]
        
        # Validate inputs
        if balance <= 0:
            await update.message.reply_text("❌ Balance must be positive", parse_mode=ParseMode.MARKDOWN)
            return
        if risk_percent <= 0 or risk_percent > 10:
            await update.message.reply_text("⚠️ Risk should be between 0.1 and 10%", parse_mode=ParseMode.MARKDOWN)
            return
        if stop_loss <= 0 or stop_loss > 1000:
            await update.message.reply_text("❌ Stop loss should be between 1 and 1000 pips", parse_mode=ParseMode.MARKDOWN)
            return
            
        # Generate response
        response = generate_lot_response(balance, risk_percent, stop_loss)
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ *Invalid Input*\n\n"
            "Please check your format and try again.\n"
            "Example: /calculate 1000 2 50",
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle balance inputs and calculate lot size."""
    text = update.message.text
    
    # Try to extract a number from the text
    number_match = re.search(r'\b\d+(?:\.\d+)?\b', text)
    
    if number_match:
        try:
            # Extract and convert to float
            balance = float(number_match.group())
            
            # Get user settings
            user_id = update.effective_chat.id
            if user_id not in user_settings:
                user_settings[user_id] = {"risk_percent": 2, "stop_loss_pips": 50}
                
            settings = user_settings[user_id]
            risk_percent = settings["risk_percent"]
            stop_loss = settings["stop_loss_pips"]
            
            # Generate response
            response = generate_lot_response(balance, risk_percent, stop_loss)
            
            # Create keyboard for additional options
            keyboard = [
                [
                    InlineKeyboardButton("Change Risk", callback_data=f"change_risk_{balance}"),
                    InlineKeyboardButton("Change Stop Loss", callback_data=f"change_sl_{balance}")
                ],
                [InlineKeyboardButton("Share Results", callback_data=f"share_{balance}_{risk_percent}_{stop_loss}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                response, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except ValueError:
            pass  # If conversion fails, just ignore it
    else:
        # Only respond with help if the message seems like a direct communication
        if update.effective_chat.type == "private" and not text.startswith("/"):
            await update.message.reply_text(
                "Please send your account balance as a number to calculate lot size.\n"
                "Example: 1000\n\n"
                "Or use /help to see all available commands.",
                parse_mode=ParseMode.MARKDOWN
            )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_chat.id
    if user_id not in user_settings:
        user_settings[user_id] = {"risk_percent": 2, "stop_loss_pips": 50}
    
    # Parse the callback data
    data = query.data
    
    if data == "set_risk":
        await query.message.reply_text(
            "*Set Your Risk Percentage*\n\n"
            "Please use the command:\n"
            "/setrisk <percentage>\n\n"
            "Example: `/setrisk 2.5`\n\n"
            "_This sets your risk to 2.5% of your account per trade._",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "set_sl":
        await query.message.reply_text(
            "*Set Your Stop Loss*\n\n"
            "Please use the command:\n"
            "/setsl <pips>\n\n"
            "Example: `/setsl 50`\n\n"
            "_This sets your default stop loss to 50 pips._",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "calc_lot":
        await query.message.reply_text(
            "*Calculate Lot Size*\n\n"
            "Simply send your account balance as a number.\n"
            "Example: `1000`\n\n"
            "For advanced calculation use:\n"
            "/calculate <balance> <risk%> <stop_loss>\n\n"
            "Example: `/calculate 1000 2.5 45`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("change_risk_"):
        balance = float(data.split("_")[2])
        await query.message.reply_text(
            f"*Change Risk for ${balance:,.2f} Balance*\n\n"
            f"Please use the command:\n"
            f"/setrisk <percentage>\n\n"
            f"Then send {balance} again to recalculate.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("change_sl_"):
        balance = float(data.split("_")[2])
        await query.message.reply_text(
            f"*Change Stop Loss for ${balance:,.2f} Balance*\n\n"
            f"Please use the command:\n"
            f"/setsl <pips>\n\n"
            f"Then send {balance} again to recalculate.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("share_"):
        parts = data.split("_")
        balance = float(parts[1])
        risk = float(parts[2])
        sl = int(parts[3])
        
        share_text = generate_lot_response(balance, risk, sl)
        await query.message.reply_text(
            "*Results Ready to Share*\n\n"
            "Forward the following message to your channel or group:",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.message.reply_text(share_text, parse_mode=ParseMode.MARKDOWN)

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("7796633438:AAFdYTwGDblhTorWAbXWgm08b-tItqN1Tss").build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("setrisk", set_risk))
    application.add_handler(CommandHandler("setsl", set_stop_loss))
    application.add_handler(CommandHandler("calculate", advanced_calculate))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handler (for balance inputs)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance))
    
    # Start the Bot
    application.run_polling()
    logger.info("Bot started")

if __name__ == "__main__":
    main()