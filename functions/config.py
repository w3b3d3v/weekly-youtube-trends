import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

print("API Keys found:")
print(f"YouTube API Key: {YOUTUBE_API_KEY}")
print(f"Firebase Project ID: {FIREBASE_PROJECT_ID}")
print(f"Google Application Credentials: {GOOGLE_APPLICATION_CREDENTIALS}")
print(f"Anthropic API Key: {ANTHROPIC_API_KEY}")
