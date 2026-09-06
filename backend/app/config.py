"""
Loads settings from a .env file (never committed — see .gitignore) so
your API key never ends up hardcoded in source or pushed to GitHub.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
