import os
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root folder
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None
downloads_col = None

if MONGO_URI:
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client["TelegramBot"]
        downloads_col = db["downloads"]
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

async def save_download(user_id: int, file_name: str, platform: str):
    if downloads_col is None: return
    try:
        await downloads_col.insert_one({
            "user_id": user_id,
            "file_name": file_name,
            "platform": platform,
            "timestamp": datetime.datetime.utcnow()
        })
    except Exception as e:
        print(f"DB Insert Error: {e}")

async def get_history(user_id: int, limit: int = 5):
    if downloads_col is None: return []
    try:
        cursor = downloads_col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    except Exception as e:
        print(f"DB History Error: {e}")
        return []

async def clear_history(user_id: int):
    if downloads_col is None: return 0
    try:
        result = await downloads_col.delete_many({"user_id": user_id})
        return result.deleted_count
    except Exception as e:
        print(f"DB Clear Error: {e}")
        return 0

async def get_today_stats():
    if downloads_col is None: return 0
    try:
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = await downloads_col.count_documents({"timestamp": {"$gte": today}})
        return count
    except Exception as e:
        print(f"DB Stats Error: {e}")
        return 0
