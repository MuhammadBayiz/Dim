import os
import asyncio
import logging
import time
from pyrogram import Client, filters
import config
from services import extractor, downloader, uploader, auth

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
    # Initial Status
    status_msg = await message.reply_text(f"🔎 **Analyzing Link...**\n`{url}`")
    
    try:
        # 1. Extract
        direct_url, headers, filename = await extractor.extract_direct_url(url)
        
        if not direct_url:
            await status_msg.edit_text(f"❌ **Extraction Failed**\nURL: `{url}`")
            return

        # 2. Setup Filename & Extension
        if not filename:
            timestamp = int(time.time())
            filename = f"video_{timestamp}_{message.id}"
        
        if "." not in filename:
            if ".mkv" in direct_url: filename += ".mkv"
            elif ".avi" in direct_url: filename += ".avi"
            else: filename += ".mp4"
            
        filename = "".join([c for c in filename if c.isalnum() or c in "._- "]).strip()
        output_path = os.path.join(config.DOWNLOAD_PATH, filename)
        
        # Update Status: Found
        await status_msg.edit_text(f"✅ **File Found**\n📄 `{filename}`\n⬇️ Starting Download...")

        # 3. Download with Progress
        async def progress(current, total, speed, eta):
            try:
                # current is percentage (0-100)
                percentage = current
                
                # Simple Visual Bar
                # [█████-----] 50%
                filled = int(percentage // 10)
                bar = '█' * filled + '-' * (10 - filled)
                
                text = (
                    f"⬇️ **Downloading...**\n"
                    f"`[{bar}]` **{percentage}%**\n\n"
                    f"🚀 Speed: **{speed}**\n"
                    f"⏳ ETA: **{eta}**\n"
                    f"📄 `{filename}`"
                )
                
                # Only edit if text changed (Pyrogram handles this check internally too)
                await status_msg.edit_text(text)
            except Exception:
                pass # Ignore flood wait errors during rapid updates

        result_path = await downloader.download_file(direct_url, headers, output_path, progress_callback=progress)

        if not result_path:
            await status_msg.edit_text(f"❌ **Download Failed**\nCheck logs for details.")
            return

        # 4. Final Success
        file_size = os.path.getsize(result_path)
        size_str = downloader.format_size(file_size)
        
        final_text = (
            f"✅ **Download Complete**\n\n"
            f"📄 `{filename}`\n"
            f"📦 Size: `{size_str}`"
        )
        await status_msg.edit_text(final_text)
        
        # Call API if enabled
        if config.ENABLE_API_UPLOAD:
            await status_msg.edit_text(final_text + "\n\n📡 Notifying API...")
            api_success = await uploader.notify_api(filename, result_path)
            api_status = "✅ Sent" if api_success else "❌ Failed"
            await status_msg.edit_text(final_text + f"\n\n📡 API: {api_status}")

    except Exception as e:
        logger.error(f"Task failed: {e}")
        await status_msg.edit_text(f"❌ **Critical Error**\n`{str(e)}`")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

# --- Admin Commands ---

def is_owner(user_id):
    return user_id == config.OWNER_ID or str(user_id) == str(config.OWNER_ID)

@app.on_message(filters.command("adduser", prefixes="/"))
async def add_user_handler(client, message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /adduser <id or username>")
        return
    
    identifier = message.command[1]
    if auth.add_user(identifier):
        await message.reply_text(f"✅ User {identifier} added.")
    else:
        await message.reply_text(f"⚠️ User {identifier} already exists.")

@app.on_message(filters.command("removeuser", prefixes="/"))
async def remove_user_handler(client, message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("Usage: /removeuser <id or username>")
        return
    
    identifier = message.command[1]
    if auth.remove_user(identifier):
        await message.reply_text(f"✅ User {identifier} removed.")
    else:
        await message.reply_text(f"⚠️ User {identifier} not found.")

@app.on_message(filters.command("listusers", prefixes="/"))
async def list_users_handler(client, message):
    if not is_owner(message.from_user.id):
        return
    
    users = auth.get_users()
    if not users:
        await message.reply_text("📂 No allowed users.")
    else:
        await message.reply_text(f"📂 Allowed Users:\n" + "\n".join([f"- `{u}`" for u in users]))

# --- Upload Handler ---

@app.on_message(filters.command("upload", prefixes="/"))
async def upload_handler(client, message):
    user = message.from_user
    if not auth.is_authorized(user.id, user.username):
        await message.reply_text("⛔ You are not authorized to use this bot.")
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: /upload <url>")
        return

    url = message.command[1]
    asyncio.create_task(process_upload_task(client, message, url))
    logger.info(f"Spawned download task for {url}")

if __name__ == "__main__":
    print("Dim Userbot started...")
    app.run()