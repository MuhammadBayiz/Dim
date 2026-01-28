# Dim Bot Project Context

## Overview
**Dim** is a specialized Telegram Bot designed to run on shared hosting environments (like seedboxes). Its primary function is to extract and download video files from streaming services (**Terabox**, **YourUpload**) directly to the local server, while providing real-time progress updates to the user via Telegram.

The project is built with **Python 3**, using **Pyrogram** for the Telegram interface and **aiohttp** for asynchronous network operations. It features a custom "Download Manager" architecture that handles extraction, filename resolution, and chunked downloading with progress reporting.

## Key Features & Architecture

### 1. Telegram Interface (`main.py`)
*   **Mode:** Standard Bot API (not Userbot).
*   **Authentication:** Uses `BOT_TOKEN` and restricts commands to a specific `OWNER_ID`.
*   **Concurrency:** Uses `asyncio.create_task` to handle multiple `/upload` requests in parallel without blocking the main event loop.
*   **Progress Tracking:** Updates the status message with a visual progress bar, speed, size, and ETA.

### 2. Extractor Service (`services/extractors/`)
A router (`services/extractor.py`) delegates URLs to specific modules:

*   **Terabox (`terabox.py`)**:
    *   **Strategy:** "Private Account Search". It does *not* use the public "Share API" (which is heavily captcha-guarded).
    *   **Workflow:**
        1.  Resolves the Share URL to get the filename.
        2.  **Recursively searches** the user's *own* Terabox account (starting from Root) to find the file. *Note: The file must be saved to the user's account first.*
        3.  Uses the **PCS (Private Cloud Storage) API** (`/rest/2.0/pcs/file`) to generate a direct download link.
    *   **Auth:** Requires a valid `ndus` cookie in `.env`.

*   **YourUpload (`yourupload.py`)**:
    *   **Strategy:** HTML Scraping.
    *   **Workflow:** Fetches the embed page and extracts the direct link from the `<meta property="og:video">` tag.

### 3. Downloader Service (`services/downloader.py`)
*   **Method:** Async chunked download using `aiohttp`.
*   **Features:**
    *   Custom timeout settings for large files.
    *   Real-time callback for progress updates.
    *   Automatic directory creation (`~/files/output/`).

## ⚠️ Critical Environment Configurations

This project is tuned for **Shared Hosting / Seedboxes** which often have restricted networking or broken IPv6/SSL configurations.

**"Nuclear" Connectivity Fixes:**
To ensure reliability on these restrictive networks, the following settings are hardcoded in `downloader.py` and all extractors:
1.  **Force IPv4:** Uses `aiohttp.TCPConnector(family=socket.AF_INET)` to bypass unstable IPv6.
2.  **Disable SSL Verification:** Sets `ssl=False` in both the connector and per-request `session.get()` calls. This is intentional to prevent `CERTIFICATE_VERIFY_FAILED` errors common on these servers.

## Build & Run

### Prerequisites
*   Python 3.10+
*   FFmpeg (optional, for future features)

### Installation
1.  **Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration (`.env`):**
    ```ini
    API_ID=...
    API_HASH=...
    BOT_TOKEN=...
    OWNER_ID=...
    TERABOX_NDUS=... (Essential for Terabox support)
    ```

3.  **Execution:**
    ```bash
    python3 main.py
    ```

## Directory Structure
```text
Dim/
├── main.py                 # Entry point, Telegram handlers
├── config.py               # Config loader
├── services/
│   ├── downloader.py       # Async downloader with progress
│   ├── extractor.py        # Logic router
│   └── extractors/
│       ├── terabox.py      # Recursive Private API extractor
│       └── yourupload.py   # Meta tag scraper
├── files/
│   └── output/             # Download destination
└── .env                    # Secrets (Excluded from Git)
```
