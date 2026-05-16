import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.getenv("CLOUD_NAME"),
    api_key    = os.getenv("CLOUD_API_KEY"),
    api_secret = os.getenv("CLOUD_API_SECRET"),
    secure     = True
)

print(f"☁️  Cloudinary configured: {os.getenv('CLOUD_NAME')}")


def upload_to_cloudinary(file_path: str, file_name: str) -> str:
    """
    Upload video/audio file to Cloudinary.
    Returns public URL.
    """
    ext        = file_name.lower().split(".")[-1]
    public_id  = file_name.replace(f".{ext}", "").replace(" ", "_")[:80]
    is_video   = ext in ["mp4", "mkv", "webm", "mov", "avi"]
    is_audio   = ext in ["mp3", "m4a", "ogg", "wav", "flac"]
    res_type   = "video" if (is_video or is_audio) else "raw"

    print(f"☁️  Uploading to Cloudinary: {file_name} ({res_type})")

    result = cloudinary.uploader.upload(
        file_path,
        public_id     = public_id,
        resource_type = res_type,
        folder        = "telegram_bot",
        overwrite     = True,
        timeout       = 300,
    )

    url = result.get("secure_url")
    print(f"✅ Cloudinary URL: {url}")

    # Delete local file after upload
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"🗑️  Deleted local: {file_name}")

    return url