from services.extractors import yourupload, terabox

async def extract_direct_url(url: str) -> tuple[str | None, dict]:
    """
    Main entry point for URL extraction. Routes to specific extractors.
    
    Args:
        url (str): The input URL (e.g., yourupload, terabox).
        
    Returns:
        tuple: (direct_stream_url, headers_dict)
    """
    if "yourupload.com" in url:
        return await yourupload.extract(url)
    
    if "terabox" in url or "1024tera" in url:
        return await terabox.extract(url)
    
    # Placeholder for future extractors
    return None, {}
