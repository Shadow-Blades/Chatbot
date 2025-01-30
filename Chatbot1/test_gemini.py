import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Get API key from environment
    api_key = "AIzaSyCsyoIZg9uIjsuabXOYAFpZR97uu1Gl974"  # Using your existing API key
    print("Configuring Gemini...")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Create models
    model = genai.GenerativeModel('gemini-pro')
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    print("Models created successfully")
    
    # Test text generation
    response = model.generate_content("Say hello and introduce yourself as a Telegram bot!")
    print("\nText generation test:")
    print(response.text)
    
    print("\nVision model is ready for image processing")
    
    # Test vision capabilities (we'll need to test this with an actual image)
    print("\nTo test image processing, you can use the vision_model with an image like this:")
    print("vision_model.generate_content(['Tell me about this image', image])")
    
except Exception as e:
    print(f"Error: {str(e)}")
    if hasattr(e, 'message'):
        print(f"Error message: {e.message}")
    if hasattr(e, 'details'):
        print(f"Error details: {e.details}")
