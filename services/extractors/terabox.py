import aiohttp
import re
import config
import asyncio
import ssl
import socket

async def extract(url: str) -> tuple[str | None, dict, str | None]:
    """
    Extracts Terabox download link by RECURSIVELY searching for the file in the user's OWN account,
    then resolving the dlink using fs_id.
    """
    if not config.TERABOX_NDUS:
        print("Error: TERABOX_NDUS cookie not found in .env")
        return None, {}, None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Cookie": f"ndus={config.TERABOX_NDUS}",
        "Referer": "https://www.terabox.com/main",
        "Accept": "application/json, text/plain, */*",
    }
    
    # Force IPv4 and Disable SSL verification
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
    
    # Custom timeout for slow connections
    timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_read=30)

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 1. Get filename (with retries)
            print(f"Terabox: Resolving URL to find filename: {url}")
            target_filename = None
            
            for attempt in range(3):
                try:
                    async with session.get(url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            html = await response.text()
                            title_match = re.search(r'<title>(.*?)</title>', html)
                            if title_match:
                                target_filename = title_match.group(1).split(" - ")[0].strip()
                                break # Success
                        else:
                            print(f"Terabox: URL resolution failed with status {response.status} (Attempt {attempt+1}/3)")
                except Exception as e:
                    print(f"Terabox: URL resolution error: {e} (Attempt {attempt+1}/3)")
                    await asyncio.sleep(2) # Wait before retry
            
            if not target_filename:
                print("Terabox: Failed to resolve filename after retries.")
                return None, {}, None

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

                async with session.get(list_url, params=params, headers=headers, ssl=False) as resp:
                    data = await resp.json()
                    if data.get("errno") != 0: continue 

                    file_list = data.get("list", [])
                    
                    for file in file_list:
                        is_dir = str(file.get("isdir", "0"))
                        server_filename = file.get("server_filename", "")

                        if is_dir == "0":
                            # Improve matching:
                            # 1. Exact match
                            # 2. Target contained in Server Filename (e.g. "Movie" in "Movie.mp4")
                            # 3. Server Filename contained in Target (rare but possible)
                            
                            match = False
                            if server_filename == target_filename:
                                match = True
                            elif target_filename in server_filename:
                                match = True
                            
                            if match:
                                path = file.get("path")
                                print(f"Terabox: Match found at path: {path}")
                                
                                # 3. Generate Link using PCS API
                                pcs_url = "https://www.terabox.com/rest/2.0/pcs/file"
                                pcs_params = {
                                    "method": "download",
                                    "path": path,
                                    "app_id": "250528"
                                }
                                
                                async with session.get(pcs_url, params=pcs_params, headers=headers, allow_redirects=False, ssl=False) as pcs_resp:
                                    if pcs_resp.status in [302, 301, 307]:
                                        redirect_url = pcs_resp.headers.get("Location")
                                        return redirect_url, headers, server_filename
                                    elif pcs_resp.status == 200:
                                        constructed_url = str(pcs_resp.url)
                                        return constructed_url, headers, server_filename
                                
                                print("Terabox: PCS API did not return a redirect.")
                                return None, {}, None

                        elif is_dir == "1":
                            folder_path = file.get("path")
                            if folder_path and folder_path != current_path:
                                queue.append(folder_path)
                
                await asyncio.sleep(0.1)

            print("Terabox: File not found.")
            return None, {}, None

    except Exception as e:
        print(f"Terabox Extraction Error: {e}")
        return None, {}, None
