import os
import asyncio
import logging
import time
from pyrogram import Client, filters
import config
from services import extractor, downloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Bot
if not config.BOT_TOKEN:
    logger.error("BOT_TOKEN is missing. Please add it to .env")
    exit(1)

app = Client(
    "dim_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

def get_progress_bar(current, total):
    if total == 0:
        return "Unknown size"
    percentage = current * 100 / total
    filled_length = int(percentage // 10) # 10 blocks for 100%
    bar = '▓' * filled_length + '░' * (10 - filled_length)
    return f"{bar} {percentage:.1f}%"

async def process_upload_task(client, message, url):
    """
    Background task: Extract -> Download -> Notify.
    """
    status_msg = await message.reply_text(f"⏳ Processing: {url}")
    
    try:
        # 1. Extract
        await status_msg.edit_text(f"🔍 Extracting URL...\n{url}")
        direct_url, headers = await extractor.extract_direct_url(url)
        
        if not direct_url:
            await status_msg.edit_text(f"❌ Extraction failed for: {url}")
            return

        # 2. Setup Filename
        timestamp = int(time.time())
        ext = ".mp4" # Default
        if ".mkv" in direct_url: ext = ".mkv"
        if ".avi" in direct_url: ext = ".avi"
        
        filename = f"video_{timestamp}_{message.id}{ext}"
        output_path = os.path.join(config.DOWNLOAD_PATH, filename)
        
        # 3. Download with Progress
        async def progress(current, total, speed, eta):
            try:
                # Format: 
                # ⬇️ Downloading...
                # ▓▓▓▓░░░░░░ 45.0%
                # 📦 Size: 50MB / 120MB
                # 🚀 Speed: 5.2 MB/s
                # ⏳ ETA: 1m 30s
                
                total_str = downloader.format_size(total) if total > 0 else "?"
                current_str = downloader.format_size(current)
                
                text = (
                    f"⬇️ **Downloading...**\n"
                    f"{get_progress_bar(current, total)}\n"
                    f"📦 {current_str} / {total_str}\n"
                    f"🚀 {speed} | ⏳ {eta}"
                )
                await status_msg.edit_text(text)
            except Exception:
                pass # Ignore edit errors (flood wait etc)

        result_path = await downloader.download_file(direct_url, headers, output_path, progress_callback=progress)

        if not result_path:
            await status_msg.edit_text("❌ Download failed.")
            return

        # 4. Final Success Message
        file_size = os.path.getsize(result_path)
        size_str = downloader.format_size(file_size)
        
        await status_msg.edit_text(
            f"✅ **Download Complete!**\n\n"
            f"📂 Saved to: `{result_path}`\n"
            f"📦 Size: {size_str}"
        )

    except Exception as e:
        logger.error(f"Task failed: {e}")
        await status_msg.edit_text(f"❌ Critical Error: {e}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

@app.on_message(filters.command("upload", prefixes="/") & filters.user(config.OWNER_ID))
async def upload_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /upload <url>")
        return

    url = message.command[1]
    asyncio.create_task(process_upload_task(client, message, url))
    logger.info(f"Spawned download task for {url}")

if __name__ == "__main__":
    print("Dim Userbot started...")
    app.run()