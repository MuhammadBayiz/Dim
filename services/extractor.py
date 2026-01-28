from services.extractors import yourupload, terabox

async def extract_direct_url(url: str) -> tuple[str | None, dict, str | None]:
    """
    Main entry point for URL extraction. Routes to specific extractors.
    
    Args:
        url (str): The input URL (e.g., yourupload, terabox).
        
    Returns:
        tuple: (direct_stream_url, headers_dict, filename)
    """
    if "yourupload.com" in url:
        return await yourupload.extract(url)
    
    if "terabox" in url or "1024tera" in url or "teraboxlink" in url:
        direct_url, headers, filename = await terabox.extract(url)
        print(f"DEBUG: Extractor returned headers: {headers}")
        return direct_url, headers, filename
    
    # Placeholder for future extractors
    return None, {}, None
