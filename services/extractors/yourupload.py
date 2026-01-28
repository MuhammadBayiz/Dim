import aiohttp
from bs4 import BeautifulSoup
import ssl
import socket

async def extract(url: str) -> tuple[str | None, dict, str | None]:
    """
    Extracts the direct video URL from a YourUpload embed/page URL.
    
    Args:
        url (str): The YourUpload URL (e.g., https://www.yourupload.com/embed/...)
        
    Returns:
        tuple: (direct_video_url, headers, filename)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.yourupload.com/"
    }

    # Force IPv4 and Disable SSL verification
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status != 200:
                    print(f"YourUpload: Failed to fetch page. Status: {response.status}")
                    return None, {}, None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Logic from Go script: find meta[property="og:video"]
                meta_tag = soup.find("meta", property="og:video")
                filename_tag = soup.find("meta", property="og:title")
                
                filename = "video.mp4"
                if filename_tag and filename_tag.get("content"):
                    filename = filename_tag["content"].strip()
                    if not filename.endswith(".mp4"):
                        filename += ".mp4"
                
                if meta_tag and meta_tag.get("content"):
                    direct_url = meta_tag["content"]
                    return direct_url, headers, filename
                
                print("YourUpload: og:video meta tag not found.")
                return None, {}, None

    except Exception as e:
        print(f"YourUpload Extraction Error: {e}")
        return None, {}, None
