import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Get the token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"Bot token: {TOKEN[:10]}...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received start command from user {update.effective_user.id}")
    await update.message.reply_text("Hello! I'm a test bot.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received message: {update.message.text}")
    await update.message.reply_text(f"You said: {update.message.text}")

def main():
    print("Starting test bot...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    print("Application created")

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Handlers added")

    # Start polling
    print("Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
