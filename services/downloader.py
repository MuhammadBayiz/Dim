import os
import logging
import asyncio
import re
import math
import time

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

def redact_url(url):
    """Redacts sensitive query parameters from URL for logging."""
    if not url: return url
    # List of sensitive keys to redact
    sensitive_keys = ["access_tokens", "ndus", "sekey", "sign"]
    
    for key in sensitive_keys:
        # Regex to replace key=value with key=REDACTED
        # Handles ?key=val and &key=val
        url = re.sub(f"([?&]{key}=)([^&]+)", f"\\1REDACTED", url)
    return url

async def download_file(url: str, headers: dict, filename: str, progress_callback=None) -> str | None:
    """
    Downloads a file using aria2c for maximum speed (multi-connection).
    Parses aria2c console output for progress updates.
    """
    safe_url = redact_url(url)
    logger.info(f"Starting aria2c download: {safe_url} -> {filename}")
    
    output_dir = os.path.dirname(filename)
    output_file = os.path.basename(filename)
    os.makedirs(output_dir, exist_ok=True)

    # Build aria2c command
    cmd = [
        "aria2c",
        "--file-allocation=none",
        "-x", "16",
        "-s", "16",
        "-j", "16",
        "-k", "1M",
        "--check-certificate=false",
        "--summary-interval=2",
        "--console-log-level=warn", # Reduce noise
        "-d", output_dir,
        "-o", output_file,
        url
    ]

    # Add headers (Cookies, User-Agent, Referer)
    logger.info(f"Passing Headers to aria2c: {headers}")
    for k, v in headers.items():
        cmd.extend(["--header", f"{k}: {v}"])

        try:

            # Create subprocess

            process = await asyncio.create_subprocess_exec(

                *cmd,

                stdout=asyncio.subprocess.PIPE,

                stderr=asyncio.subprocess.PIPE

            )

    

            # Updated Regex to handle spaces in percentage

            # Matches: 1.5GiB/2.5GiB( 60%) ... 3.2MiB/s

            status_pattern = re.compile(r"([\d\.]+[KMG]?i?B)/([\d\.]+[KMG]?i?B)\(\s*(\d+)%\).*?DL:([\d\.]+[KMG]?i?B)/s(?:.*?ETA:([a-zA-Z0-9:]+))?")

    

            last_percent = -1

            last_update_time = 0

    

            while True:

                line_bytes = await process.stdout.readline()

                if not line_bytes:

                    break

                

                line = line_bytes.decode('utf-8', errors='ignore').strip()

                

                if not line:

                    continue

    

                match = status_pattern.search(line)

                if match and progress_callback:

                    percent = int(match.group(3))

                    speed = match.group(4)

                    eta = match.group(5) or "?"

    

                    current_time = time.time()

                    # Update if percent changed OR if 2 seconds passed

                    if percent != last_percent or (current_time - last_update_time >= 2):

                        try:

                            await progress_callback(

                                percent,   

                                100,       

                                speed + "/s", 

                                eta

                            )

                            last_percent = percent

                            last_update_time = current_time

                        except Exception as e:

                            logger.error(f"Callback error: {e}")

    

            await process.wait()

    

            if process.returncode == 0:

                logger.info(f"aria2c download complete: {filename}")

                return filename

            else:

                stderr = await process.stderr.read()

                logger.error(f"aria2c failed with code {process.returncode}: {stderr.decode()}")

                return None

    

        except asyncio.CancelledError:

            logger.warning(f"Download cancelled: {filename}")

            if process:

                process.terminate()

                try:

                    await process.wait() # Wait for it to die

                except:

                    pass

            

            # Clean up partial files

            if os.path.exists(filename):

                os.remove(filename)

            if os.path.exists(filename + ".aria2"):

                os.remove(filename + ".aria2")

            raise # Re-raise to let main.py know

    

        except Exception as e:

            logger.error(f"Error during aria2c download: {e}")

            return None

    