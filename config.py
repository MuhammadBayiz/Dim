import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
TERABOX_NDUS = os.getenv("TERABOX_NDUS")
DOWNLOAD_PATH = os.path.expanduser("~/files/output/")

# Validate required config
if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID]):
    print("Warning: API_ID, API_HASH, BOT_TOKEN or OWNER_ID are missing in .env")
