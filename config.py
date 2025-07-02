import os

# Load API keys and settings from environment or defaults
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-default-key')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
