import os
import logging
import asyncio
import re

# Configure logger
logger = logging.getLogger(__name__)

async def download_file(url: str, headers: dict, filename: str, progress_callback=None) -> str | None:
    """
    Downloads a file using aria2c for maximum speed (multi-connection).
    Parses aria2c console output for progress updates.
    """
    logger.info(f"Starting aria2c download: {url} -> {filename}")
    
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

        # Updated Regex to be more flexible
        # Captures: 25MiB/1.5GiB(1%) ... DL:3.2MiB/s ... ETA:7m50s
        status_pattern = re.compile(r"([\d\.]+[KMG]?i?B)/([\d\.]+[KMG]?i?B)\((\d+)%\).*?DL:([\d\.]+[KMG]?i?B)/s.*?ETA:([a-zA-Z0-9:]+)")

        last_percent = -1

        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            
            # Skip empty lines
            if not line:
                continue

            # DEBUG: Print raw line to see what aria2c is outputting
            logger.info(f"RAW ARIA2: {line}") 

            match = status_pattern.search(line)
            if match and progress_callback:
                downloaded_str = match.group(1)
                total_str = match.group(2)
                percent = int(match.group(3))
                speed = match.group(4)
                eta = match.group(5)

                if percent != last_percent:
                    try:
                        await progress_callback(
                            percent,   
                            100,       
                            speed + "/s", 
                            eta
                        )
                        last_percent = percent
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

        await process.wait()

        if process.returncode == 0:
            logger.info(f"aria2c download complete: {filename}")
            return filename
        else:
            # Read any error output
            stderr = await process.stderr.read()
            logger.error(f"aria2c failed with code {process.returncode}: {stderr.decode()}")
            return None

    except Exception as e:
        logger.error(f"Error during aria2c download: {e}")
        return None