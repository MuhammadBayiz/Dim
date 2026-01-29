import aiohttp
import jwt
import logging
import config

logger = logging.getLogger(__name__)

async def notify_api(filename: str, filepath: str):
    """
    Sends a notification to the external API after download completion.
    """
    if not all([config.API_URL, config.API_USERNAME, config.API_SECRET]):
        logger.warning("API config missing. Skipping upload notification.")
        return

    payload = {
        "fileName": filename,
        "filePath": filepath
    }

    try:
        encoded_jwt = jwt.encode(
            {"user": {"username": config.API_USERNAME, "label": ""}}, 
            config.API_SECRET, 
            algorithm="HS256"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {encoded_jwt}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(config.API_URL, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    logger.info(f"API Notification Success: {response.status}")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"API Notification Failed: {response.status} - {text}")
                    return False

    except Exception as e:
        logger.error(f"API Notification Error: {e}")
        return False
