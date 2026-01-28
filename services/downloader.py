import aiohttp
import os
import time
import logging
import math
import ssl
import socket

# Configure logger
logger = logging.getLogger(__name__)

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

async def download_file(url: str, headers: dict, filename: str, progress_callback=None) -> str | None:
    """
    Downloads a file with progress reporting via callback.
    
    Args:
        progress_callback: async function(current, total, speed, eta)
    """
    logger.info(f"Starting download: {url} -> {filename}")
    start_time = time.time()
    
    # Force IPv4 and Disable SSL verification
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
    
    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=60, sock_read=300)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(url, headers=headers) as response:
                if response.status not in [200, 206]:
                    logger.error(f"Download failed. Status: {response.status}")
                    return None
                
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded_size = 0
                last_update_time = time.time()
                
                # Create directory if needed
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                with open(filename, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024): # 1MB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        current_time = time.time()
                        if progress_callback and (current_time - last_update_time > 3 or downloaded_size == total_size):
                            elapsed = current_time - start_time
                            speed = downloaded_size / elapsed if elapsed > 0 else 0 # bytes/sec
                            
                            eta = 0
                            if speed > 0 and total_size > 0:
                                eta = (total_size - downloaded_size) / speed
                                
                            await progress_callback(
                                downloaded_size, 
                                total_size, 
                                format_size(speed) + "/s", 
                                format_time(eta)
                            )
                            last_update_time = current_time

        logger.info(f"Download complete: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error during download of {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return None
