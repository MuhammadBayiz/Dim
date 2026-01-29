import os
import asyncio
import logging
import time
from pyrogram import Client, filters
import config
from services import extractor, downloader, uploader

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
        direct_url, headers, filename = await extractor.extract_direct_url(url)
        
        if not direct_url:
            await status_msg.edit_text(f"❌ Extraction failed for: {url}")
            return

        # 2. Setup Filename & Extension
        if not filename:
            timestamp = int(time.time())
            filename = f"video_{timestamp}_{message.id}"
        
        # Ensure extension exists
        if "." not in filename:
            # Try to guess from URL or default to mp4
            if ".mkv" in direct_url: filename += ".mkv"
            elif ".avi" in direct_url: filename += ".avi"
            else: filename += ".mp4"
            
        # Ensure filename is safe for filesystem
        filename = "".join([c for c in filename if c.isalnum() or c in "._- "]).strip()
        output_path = os.path.join(config.DOWNLOAD_PATH, filename)
        
        # 3. Download with Progress
        async def progress(current, total, speed, eta):
            try:
                # If total is 100, it means aria2c sent us a percentage directly
                if total == 100:
                    percentage = current
                    filled_length = int(percentage // 10)
                    bar = '▓' * filled_length + '░' * (10 - filled_length)
                    text = (
                        f"⬇️ **Downloading (aria2c)**\n"
                        f"{bar} {percentage}%\n"
                        f"🚀 {speed} | ⏳ {eta}"
                    )
                else:
                    # Legacy fallback
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
                pass # Ignore edit errors

        result_path = await downloader.download_file(direct_url, headers, output_path, progress_callback=progress)

        if not result_path:
            await status_msg.edit_text("❌ Download failed.")
            return

        # 4. Final Success Message & API Notification
        file_size = os.path.getsize(result_path)
        size_str = downloader.format_size(file_size)
        
        await status_msg.edit_text(
            f"✅ **Download Complete!**\n\n"
            f"📂 Saved to: `{result_path}`\n"
            f"📦 Size: {size_str}\n\n"
            f"📡 Notifying API..."
        )
        
        # Call API
        api_success = await uploader.notify_api(filename, result_path)
        
        status_text = (
            f"✅ **Task Completed**\n\n"
            f"📂 File: `{filename}`\n"
            f"📦 Size: {size_str}\n"
            f"📡 API: {'✅ Sent' if api_success else '❌ Failed'}"
        )
        await status_msg.edit_text(status_text)

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