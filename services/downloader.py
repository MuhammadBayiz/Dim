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
    
    # Ensure directory exists
    output_dir = os.path.dirname(filename)
    output_file = os.path.basename(filename)
    os.makedirs(output_dir, exist_ok=True)

    # Build aria2c command
    cmd = [
        "aria2c",
        "--file-allocation=none",
        "-x", "16",       # Max connections per server
        "-s", "16",       # Split file into 16 parts
        "-j", "16",       # Max concurrent downloads
        "-k", "1M",       # Min split size
        "--check-certificate=false", # Disable SSL verify (Host compatibility)
        "--summary-interval=2",      # Status update interval (seconds)
        "-d", output_dir,
        "-o", output_file,
        url
    ]

    # Add headers (Cookies, User-Agent, Referer)
    # aria2c takes headers as: --header "Name: Value"
    for k, v in headers.items():
        cmd.extend(["--header", f"{k}: {v}"])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Regex to parse aria2c status line:
        # [#2089b0 25MiB/1.5GiB(1%) CN:8 DL:3.2MiB/s ETA:7m50s]
        # Groups: 1=Downloaded, 2=Total, 3=Percent, 4=Speed, 5=ETA
        status_pattern = re.compile(r"\[.*?(\d+\.?\d*[KMGT]?i?B)/(\d+\.?\d*[KMGT]?i?B)\((\d+)%\).*?DL:(\d+\.?\d*[KMGT]?i?B)/s.*?ETA:([a-zA-Z0-9]+)\]")

        last_percent = -1

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            line_str = line.decode().strip()
            
            # Log output for debug (optional, can be noisy)
            # logger.info(f"aria2c: {line_str}")

            match = status_pattern.search(line_str)
            if match and progress_callback:
                downloaded_str = match.group(1)
                total_str = match.group(2)
                percent = int(match.group(3))
                speed = match.group(4)
                eta = match.group(5)

                # Only update Telegram if percentage changed to avoid flood
                if percent != last_percent:
                    # Convert strings to simpler format if needed, but strings are fine for display
                    # We pass dummy integers for current/total because formatting is already done by aria2
                    # The callback in main.py expects (current, total, speed, eta)
                    # We will pass the strings directly and handle them in main.py or adapt here.
                    
                    # NOTE: main.py expects integers for the progress bar calculation.
                    # We can pass `percent` as current and `100` as total to simplify.
                    
                    await progress_callback(
                        percent,   # current (as percentage)
                        100,       # total (as percentage base)
                        speed + "/s", 
                        eta
                    )
                    last_percent = percent

        await process.wait()

        if process.returncode == 0:
            logger.info(f"aria2c download complete: {filename}")
            return filename
        else:
            stderr = await process.stderr.read()
            logger.error(f"aria2c failed with code {process.returncode}: {stderr.decode()}")
            return None

    except Exception as e:
        logger.error(f"Error during aria2c download: {e}")
        return None
