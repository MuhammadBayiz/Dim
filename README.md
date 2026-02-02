# Dim Bot 📥

Dim Bot is a high-performance Telegram Userbot designed to extract and download videos from various streaming services directly to your local server. It supports parallel processing, real-time progress tracking, and specialized extraction logic for difficult sites like Terabox.

## 🚀 Features

*   **Multi-Source Extraction**:
    *   **Terabox**: Advanced extraction using your own account's private file list (Recursive Search & PCS API) to bypass "verify_v2" captchas.
    *   **YourUpload**: Direct video extraction.
*   **Parallel Downloads**: Handle multiple `/upload` requests simultaneously without blocking.
*   **Real-Time Progress**: Telegram messages update live with download speed, ETA, and a visual progress bar.
*   **Smart File Management**: Automatically renames files and saves them to a configured local directory.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/Dim.git
    cd Dim
    ```

2.  **Install Dependencies**
    ```bash
    pip3 install -r requirements.txt
    ```

3.  **Configuration**
    Create a `.env` file in the root directory:
    ```ini
    API_ID=your_telegram_api_id
    API_HASH=your_telegram_api_hash
    BOT_TOKEN=your_bot_token_from_botfather
    OWNER_ID=your_telegram_user_id
    TERABOX_ACCESS_TOKEN=your_premium_token
    ```
    *   **API_ID/HASH**: Get from [my.telegram.org](https://my.telegram.org).
    *   **BOT_TOKEN**: Create a bot via [@BotFather](https://t.me/BotFather).
    *   **OWNER_ID**: Get your numerical ID from [@userinfobot](https://t.me/userinfobot).
    *   **TERABOX_ACCESS_TOKEN**: Get from Terabox Developer Portal or extracted from network calls.

4.  **Run the Bot**
    ```bash
    python3 main.py
    ```

## 🎮 Usage

Send a command to your Userbot (saved messages or any chat):

```text
/upload https://teraboxlink.com/s/1...
/upload https://www.yourupload.com/embed/...
```

The bot will:
1.  Reply "⏳ Processing..."
2.  Find the file (resolving short links if needed).
3.  Download it to `~/files/output/` (configurable in `config.py`).
4.  Update the message with progress.
5.  Notify you when finished.

## ⚠️ Notes for Terabox

For the Terabox extractor to work:
1.  The file **MUST** be in your Terabox account (saved/imported).
2.  The bot searches your account for the filename found in the share link.
3.  Ensure your `TERABOX_NDUS` cookie is fresh (refresh monthly).

## 📄 License

MIT
