import yt_dlp
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from root folder
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Always use absolute path for downloads
RAW_PATH = os.getenv("DOWNLOADS_PATH", "./downloads")
DOWNLOADS_PATH = os.path.abspath(RAW_PATH)

# Make sure downloads folder exists
os.makedirs(DOWNLOADS_PATH, exist_ok=True)

print(f"📁 Downloader saving to: {DOWNLOADS_PATH}")

ACTIVE_DOWNLOADS = {}

def download_video(url: str, quality: str, user_id: int = None) -> tuple:
    """
    Download video using yt-dlp.
    Returns: (file_path, file_name, file_size)
    """
    timestamp = str(int(time.time()))

    if quality == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOADS_PATH, f"{timestamp}_%(title).50s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": False,
            "no_warnings": True,
        }
    else:
        height = quality
        ydl_opts = {
            "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
            "outtmpl": os.path.join(DOWNLOADS_PATH, f"{timestamp}_%(title).50s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": False,
            "no_warnings": True,
        }

    if user_id:
        ACTIVE_DOWNLOADS[user_id] = True

    def progress_hook(d):
        if user_id and not ACTIVE_DOWNLOADS.get(user_id, True):
            raise Exception("Download cancelled by user")

    ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    finally:
        if user_id in ACTIVE_DOWNLOADS:
            del ACTIVE_DOWNLOADS[user_id]

    # Find the downloaded file by timestamp prefix
    file_path = _find_downloaded_file(DOWNLOADS_PATH, timestamp)

    if not file_path:
        # List what's in the folder for debugging
        files = os.listdir(DOWNLOADS_PATH)
        print(f"📁 Files in downloads folder: {files}")
        raise Exception(f"File not found after download in {DOWNLOADS_PATH}")

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    print(f"✅ Downloaded: {file_name} ({round(file_size/1024/1024, 2)} MB)")
    print(f"📄 Full path: {file_path}")

    return file_path, file_name, file_size


def _find_downloaded_file(folder: str, timestamp: str):
    """Find the file that was just downloaded by matching timestamp prefix."""
    for filename in os.listdir(folder):
        if filename.startswith(timestamp):
            return os.path.join(folder, filename)
    return None