import os
import pathlib
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_vision():
    try:
        # Configure Gemini with API key
        api_key = "AIzaSyCsyoIZg9uIjsuabXOYAFpZR97uu1Gl974"
        genai.configure(api_key=api_key)
        
        # First test text generation
        text_model = genai.GenerativeModel('gemini-pro')
        text_response = text_model.generate_content("What can you do with images?")
        print("\nText Model Test:")
        print(text_response.text)
        
        # Now test vision model with the new version
        vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create a simple test image with PIL
        img = Image.new('RGB', (100, 100), color='red')
        img.save('test_image.png')
        
        # Load the test image
        img = Image.open('test_image.png')
        
        # Generate content about the image
        vision_response = vision_model.generate_content(["What color is this image?", img])
        print("\nVision Model Test:")
        print(vision_response.text)
        
        # Clean up test image
        os.remove('test_image.png')
        
        print("\nBoth models tested successfully!")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        print("\nTrying alternative vision model...")
        try:
            # Try with gemini-1.5-pro-vision as fallback
            vision_model = genai.GenerativeModel('gemini-1.5-pro-vision')
            img = Image.open('test_image.png')
            vision_response = vision_model.generate_content(["What color is this image?", img])
            print("\nVision Model Test (using alternative model):")
            print(vision_response.text)
            os.remove('test_image.png')
        except Exception as e2:
            print(f"Alternative model also failed: {str(e2)}")

if __name__ == "__main__":
    test_vision()
