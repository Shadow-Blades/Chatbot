import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure bot
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me a message and I will respond using Gemini AI.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    try:
        user_message = update.message.text
        print(f"Received message: {user_message}")
        
        # Get response from Gemini
        print("Asking Gemini...")
        response = model.generate_content(user_message)
        print("Got response from Gemini")
        
        # Send response
        await update.message.reply_text(response.text)
        print("Sent response to user")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    """Start the bot."""
    print("Starting bot...")
    print(f"Using Telegram token: {BOT_TOKEN[:10]}...")
    print(f"Using Gemini API key: {GEMINI_API_KEY[:10]}...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
