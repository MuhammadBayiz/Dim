import aiohttp
from bs4 import BeautifulSoup

async def extract(url: str) -> tuple[str | None, dict]:
    """
    Extracts the direct video URL from a YourUpload embed/page URL.
    
    Args:
        url (str): The YourUpload URL (e.g., https://www.yourupload.com/embed/...)
        
    Returns:
        tuple: (direct_video_url, headers)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.yourupload.com/"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"YourUpload: Failed to fetch page. Status: {response.status}")
                    return None, {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Logic from Go script: find meta[property="og:video"]
                meta_tag = soup.find("meta", property="og:video")
                if meta_tag and meta_tag.get("content"):
                    direct_url = meta_tag["content"]
                    return direct_url, headers
                
                print("YourUpload: og:video meta tag not found.")
                return None, {}

    except Exception as e:
        print(f"YourUpload Extraction Error: {e}")
        return None, {}
