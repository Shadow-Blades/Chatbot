import os
import io
import sys
import PIL.Image
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import google.generativeai as genai
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyCsyoIZg9uIjsuabXOYAFpZR97uu1Gl974"  # Your API key

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'telegram_bot'
USERS_COLLECTION = 'users'
CHATS_COLLECTION = 'chats'

# Initialize global variables
model = None
vision_model = None
db = None
users_collection = None
chats_collection = None

# Configure Gemini
try:
    # Configure with API key
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Initialize models
    model = genai.GenerativeModel('gemini-pro')
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    logger.info("Successfully initialized Gemini models")
except Exception as e:
    logger.error(f"Error initializing Gemini: {e}")
    raise

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION]
    chats_collection = db[CHATS_COLLECTION]
    logger.info("Successfully connected to MongoDB")
except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {e}")
    raise
except Exception as e:
    logger.error(f"Error setting up MongoDB: {e}")
    raise

# Conversation states
FIRSTNAME, LASTNAME, PHONE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [[KeyboardButton(text="Share Contact", request_contact=True)]]
    
    await update.message.reply_text(
        'Hi! I am your AI assistant. Let\'s start with your registration.\n\nWhat is your first name?',
        reply_markup=ReplyKeyboardRemove(),
    )
    return FIRSTNAME

async def firstname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['firstname'] = update.message.text
    
    await update.message.reply_text(
        'Great! Now, please tell me your last name, or send /skip if you don\'t want to share it.',
    )
    return LASTNAME

async def skip_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['lastname'] = ''
    
    reply_keyboard = [[KeyboardButton(text="Share Contact", request_contact=True)]]
    await update.message.reply_text(
        'I see! Please share your contact, or send /skip.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PHONE

async def lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['lastname'] = update.message.text
    
    reply_keyboard = [[KeyboardButton(text="Share Contact", request_contact=True)]]
    await update.message.reply_text(
        'Great! Now, please share your contact, or send /skip.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
    
    context.user_data['phone'] = phone_number
    
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # Store user data in MongoDB
    user_data = {
        "user_id": user_id,
        "telegram_id": user.id,
        "firstname": context.user_data.get('firstname', ''),
        "lastname": context.user_data.get('lastname', ''),
        "phone": phone_number,
        "username": user.username,
        "registered_at": datetime.utcnow()
    }
    
    try:
        users_collection.insert_one(user_data)
        await update.message.reply_text(
            'Thank you! You are now registered. You can start chatting with me!\n\n'
            'Send me messages and I will respond using AI.\n'
            'Send me images and I will analyze them.\n'
            'Use /help to see all available commands.',
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as e:
        logger.error(f"Error storing user data: {e}")
        await update.message.reply_text(
            'Sorry, there was an error during registration. Please try again later.',
            reply_markup=ReplyKeyboardRemove(),
        )
    
    return ConversationHandler.END

async def skip_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    
    # Generate a unique user ID
    user_id = str(uuid.uuid4())
    
    # Store user data in MongoDB
    user_data = {
        "user_id": user_id,
        "telegram_id": user.id,
        "firstname": context.user_data.get('firstname', ''),
        "lastname": context.user_data.get('lastname', ''),
        "phone": '',
        "username": user.username,
        "registered_at": datetime.utcnow()
    }
    
    try:
        users_collection.insert_one(user_data)
        await update.message.reply_text(
            'Thank you! You are now registered. You can start chatting with me!\n\n'
            'Send me messages and I will respond using AI.\n'
            'Send me images and I will analyze them.\n'
            'Use /help to see all available commands.',
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as e:
        logger.error(f"Error storing user data: {e}")
        await update.message.reply_text(
            'Sorry, there was an error during registration. Please try again later.',
            reply_markup=ReplyKeyboardRemove(),
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Registration cancelled. You can start again with /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Check if user is registered
        user = update.effective_user
        user_data = users_collection.find_one({"telegram_id": user.id})
        if not user_data:
            await update.message.reply_text(
                "Please register first using the /start command!"
            )
            return
        
        # Store user message in chat history
        chat_entry = {
            "user_id": user_data["user_id"],
            "telegram_id": user.id,
            "message": update.message.text,
            "timestamp": datetime.utcnow(),
            "type": "user"
        }
        chats_collection.insert_one(chat_entry)
        
        # Get response from Gemini
        response = model.generate_content(update.message.text)
        
        if not response.text:
            raise ValueError("Empty response received from Gemini")
        
        # Store bot response in chat history
        bot_chat_entry = {
            "user_id": user_data["user_id"],
            "telegram_id": user.id,
            "message": response.text,
            "timestamp": datetime.utcnow(),
            "type": "bot"
        }
        chats_collection.insert_one(bot_chat_entry)
        
        # Send response to user
        await update.message.reply_text(response.text)
        
    except Exception as e:
        error_message = f"Sorry, I encountered an error: {str(e)}"
        logger.error(f"Error in message handling: {str(e)}", exc_info=True)
        await update.message.reply_text(error_message)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if vision_model is None:
            await update.message.reply_text(
                "Sorry, image analysis is not available right now."
            )
            return
        
        # Check if user is registered
        user = update.effective_user
        user_data = users_collection.find_one({"telegram_id": user.id})
        if not user_data:
            await update.message.reply_text(
                "Please register first using the /start command!"
            )
            return

        await update.message.reply_text("Analyzing your image... Please wait.")
        
        # Get the photo with highest resolution
        photo = update.message.photo[-1]
        
        # Get file from Telegram
        file = await context.bot.get_file(photo.file_id)
        
        # Download the image data
        image_bytes = await file.download_as_bytearray()
        
        try:
            # Convert to PIL Image
            image = PIL.Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get description from user if provided
            prompt = "Analyze this image and describe what you see in detail."
            if update.message.caption:
                prompt = f"{update.message.caption}\nAnalyze this image based on the above context."
            
            # Generate response using Gemini Vision
            response = vision_model.generate_content([prompt, image])
            
            if not response.text:
                raise ValueError("Empty response received from Gemini Vision")
            
            # Store the interaction in chat history
            chat_entry = {
                "user_id": user_data["user_id"],
                "telegram_id": user.id,
                "message": "[Image Analysis Request]" + (f": {update.message.caption}" if update.message.caption else ""),
                "timestamp": datetime.utcnow(),
                "type": "user"
            }
            chats_collection.insert_one(chat_entry)
            
            bot_chat_entry = {
                "user_id": user_data["user_id"],
                "telegram_id": user.id,
                "message": response.text,
                "timestamp": datetime.utcnow(),
                "type": "bot"
            }
            chats_collection.insert_one(bot_chat_entry)
            
            # Send the analysis
            await update.message.reply_text(response.text)
            
        except PIL.UnidentifiedImageError:
            await update.message.reply_text("Sorry, I couldn't process this image. Please make sure it's a valid image file.")
            return
            
    except Exception as e:
        error_message = f"Sorry, I encountered an error analyzing the image: {str(e)}"
        logger.error(f"Error in image analysis: {str(e)}", exc_info=True)
        await update.message.reply_text(error_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the available commands:\n\n"
        "/start - Register as a new user\n"
        "/help - Show this help message\n\n"
        "You can also:\n"
        "- Send me text messages to chat\n"
        "- Send me images to analyze them\n"
        "- Add captions to images for specific analysis"
    )

async def main() -> None:
    """Start the bot."""
    try:
        logger.info("Starting bot...")
        
        # Validate dependencies
        if model is None or vision_model is None:
            raise RuntimeError("Gemini models not properly initialized")
        if users_collection is None or chats_collection is None:
            raise RuntimeError("MongoDB collections not properly initialized")
        
        # Create the Application
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )
        
        # Add conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                FIRSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, firstname)],
                LASTNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, lastname),
                    CommandHandler('skip', skip_lastname)
                ],
                PHONE: [
                    MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, phone),
                    CommandHandler('skip', skip_phone)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        application.add_handler(conv_handler)
        
        # Add other handlers
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Start the Bot
        logger.info("Starting polling...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
