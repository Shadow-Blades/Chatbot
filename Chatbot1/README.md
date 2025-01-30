# Telegram Bot with Gemini AI

A Telegram bot that uses Google's Gemini AI for chat responses and stores conversations in MongoDB.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Required Credentials**
   - Create a Telegram bot through [BotFather](https://t.me/botfather) and get the bot token
   - Set up a Google Cloud Project and create a service account:
     1. Go to [Google Cloud Console](https://console.cloud.google.com)
     2. Create a new project or select an existing one
     3. Enable the Vertex AI API for your project
     4. Create a service account and download the JSON key file
     5. Rename the downloaded JSON key file to `vertex-api-key.json`

3. **Set Up Environment Variables**
   - Copy `.env.example` to `.env`
   - Add your Telegram bot token
   - Place the `vertex-api-key.json` file in the project root directory
   - Update MongoDB URI if needed (default is `mongodb://localhost:27017/`)

4. **Start MongoDB**
   - Make sure MongoDB is running on your system
   - Default connection is `mongodb://localhost:27017/`

5. **Run the Bot**
   ```bash
   python bot.py
   ```

## Features
- Chat with Gemini AI (text and vision capabilities)
- Image analysis using Gemini Pro Vision
- Stores chat history in MongoDB
- Basic command handling (/start, /help)

## Security Notes
- Keep your `vertex-api-key.json` secure and never commit it to version control
- The `.gitignore` file is configured to exclude sensitive files
- Use environment variables for all sensitive credentials

## Free Features
- Telegram Bot API - Free
- Google Cloud/Vertex AI - Free tier available
- MongoDB - Free for local development
- Bot Hosting - Can be hosted locally for free

## Requirements
- Python 3.7+
- MongoDB
- Internet connection for API access
- Google Cloud account with Vertex AI API enabled
