import aiohttp
import config
import ssl
import socket
from urllib.parse import urlparse, parse_qs

async def extract(url: str) -> tuple[str | None, dict, str | None]:
    """
    Extracts Terabox download link using the Official OpenAPI (Premium Access Token).
    Flow: shorturl -> shorturlinfo (get fs_id) -> api/download (get dlink).
    """
    if not config.TERABOX_ACCESS_TOKEN:
        print("Error: TERABOX_ACCESS_TOKEN not found in .env")
        return None, {}, None

    # Common headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    
    # Connection setup
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 1. Parse 'surl' from URL
            # URL format: https://teraboxlink.com/s/1q2BnpByprnmRYk8xitPNUQ
            # surl: q2BnpByprnmRYk8xitPNUQ (after /s/1 or /s/)
            
            parsed = urlparse(url)
            surl = ""
            if "/s/" in parsed.path:
                parts = parsed.path.split("/s/")
                if len(parts) > 1:
                    surl = parts[1]
            
            # Query param fallback
            if not surl:
                qs = parse_qs(parsed.query)
                surl = qs.get("surl", [""])[0]

            # The OpenAPI shorturl parameter usually INCLUDES the leading '1'
            # e.g. https://terabox.com/s/1ABC -> shorturl=1ABC
            # So we DO NOT strip it.
            
            if not surl:
                print(f"Terabox API: Could not extract surl from {url}")
                return None, {}, None

            print(f"Terabox API: Extracted surl: {surl}")

            # 2. Call shorturlinfo to get fs_id and filename
            # Endpoint: /openapi/api/shorturlinfo
            info_url = "https://www.terabox.com/openapi/api/shorturlinfo"
            info_params = {
                "shorturl": surl,
                "root": "1",
                "access_tokens": config.TERABOX_ACCESS_TOKEN
            }

            fs_id = None
            filename = None

            async with session.get(info_url, params=info_params, headers=headers, ssl=False) as resp:
                data = await resp.json()
                if data.get("errno") != 0:
                    print(f"Terabox API Error (shorturlinfo): {data}")
                    return None, {}, None
                
                file_list = data.get("list", [])
                if not file_list:
                    print("Terabox API: No files found in share link.")
                    return None, {}, None
                
                # Pick first file
                target_file = file_list[0]
                fs_id = target_file.get("fs_id")
                filename = target_file.get("server_filename")
                
                print(f"Terabox API: Found file '{filename}' (fs_id: {fs_id})")

            if not fs_id:
                return None, {}, None

            # 3. Call download API to get dlink
            # Endpoint: /openapi/api/download
            dl_api_url = "https://www.terabox.com/openapi/api/download"
            dl_params = {
                "access_tokens": config.TERABOX_ACCESS_TOKEN,
                "fidlist": f"[{fs_id}]", # Must be a JSON array string
                "type": "dlink"
            }

            async with session.get(dl_api_url, params=dl_params, headers=headers, ssl=False) as resp:
                data = await resp.json()
                if data.get("errno") != 0:
                    print(f"Terabox API Error (download): {data}")
                    return None, {}, None
                
                dlink_list = data.get("dlink", [])
                if not dlink_list:
                    print("Terabox API: No dlink returned.")
                    return None, {}, None
                
                direct_link = dlink_list[0].get("dlink")
                if direct_link:
                    # Update filename with info from this endpoint if available (sometimes more accurate)
                    if "file_info" in data and "filename" in data["file_info"]:
                        filename = data["file_info"]["filename"]
                    
                    return direct_link, headers, filename
                
                return None, {}, None

    except Exception as e:
        print(f"Terabox API Exception: {e}")
        return None, {}, None
