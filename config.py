import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
TERABOX_NDUS = os.getenv("TERABOX_NDUS")
DOWNLOAD_PATH = os.path.expanduser("~/files/output/")

# Validate required config
if not all([API_ID, API_HASH, SESSION_STRING]):
    print("Warning: API_ID, API_HASH, or SESSION_STRING are missing in .env")
