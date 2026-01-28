import aiohttp
import re
import config
import asyncio

async def extract(url: str) -> tuple[str | None, dict]:
    """
    Extracts Terabox download link using the PCS (Private Cloud Storage) API.
    """
    if not config.TERABOX_NDUS:
        print("Error: TERABOX_NDUS cookie not found in .env")
        return None, {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Cookie": f"ndus={config.TERABOX_NDUS}",
        "Referer": "https://www.terabox.com/main",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Get filename
            print(f"Terabox: Resolving URL to find filename: {url}")
            target_filename = None
            async with session.get(url, headers=headers) as response:
                html = await response.text()
                title_match = re.search(r'<title>(.*?)</title>', html)
                if title_match:
                    target_filename = title_match.group(1).split(" - ")[0].strip()

            if not target_filename:
                return None, {}

            # 2. Recursive Search
            queue = ["/"]
            checked_folders = 0
            MAX_FOLDERS = 100
            
            print(f"Terabox: Searching for '{target_filename}'...")

            while queue and checked_folders < MAX_FOLDERS:
                current_path = queue.pop(0)
                checked_folders += 1
                
                list_url = "https://www.terabox.com/api/list"
                params = {
                    "dir": current_path,
                    "web": "1",
                    "root": "1",
                    "order": "time",
                    "desc": "1",
                    "num": "1000"
                }

                async with session.get(list_url, params=params, headers=headers) as resp:
                    data = await resp.json()
                    if data.get("errno") != 0: continue 

                    file_list = data.get("list", [])
                    
                    for file in file_list:
                        is_dir = str(file.get("isdir", "0"))
                        server_filename = file.get("server_filename")

                        if is_dir == "0":
                            if server_filename == target_filename:
                                path = file.get("path")
                                print(f"Terabox: Match found at path: {path}")
                                
                                # 3. Generate Link using PCS API
                                # This is the direct API for file operations
                                pcs_url = "https://www.terabox.com/rest/2.0/pcs/file"
                                pcs_params = {
                                    "method": "download",
                                    "path": path,
                                    "app_id": "250528"
                                }
                                
                                # Note: This usually returns the binary stream directly OR a redirect.
                                # We check if it gives us a usable URL.
                                async with session.get(pcs_url, params=pcs_params, headers=headers, allow_redirects=False) as pcs_resp:
                                    if pcs_resp.status in [302, 301, 307]:
                                        redirect_url = pcs_resp.headers.get("Location")
                                        return redirect_url, headers
                                    elif pcs_resp.status == 200:
                                        # If it returns 200, it might be the file content itself.
                                        # In that case, we can return the constructed URL as the "Direct Link"
                                        # But we need to ensure the downloader uses the same params.
                                        constructed_url = str(pcs_resp.url)
                                        return constructed_url, headers
                                
                                print("Terabox: PCS API did not return a redirect.")
                                return None, {}

                        elif is_dir == "1":
                            folder_path = file.get("path")
                            if folder_path and folder_path != current_path:
                                queue.append(folder_path)
                
                await asyncio.sleep(0.1)

            print("Terabox: File not found.")
            return None, {}

    except Exception as e:
        print(f"Terabox Extraction Error: {e}")
        return None, {}
