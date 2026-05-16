# Run this once to get your Telegram user ID
# python get_my_id.py
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

token = os.getenv("BOT_TOKEN")
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
updates = r.json().get("result", [])

if updates:
    user = updates[-1]["message"]["from"]
    print(f"Your Telegram User ID: {user['id']}")
    print(f"Your Name: {user.get('first_name')} {user.get('last_name','')}")
    print(f"\nAdd this to your .env file:")
    print(f"ADMIN_ID={user['id']}")
else:
    print("No updates found. Send any message to your bot first, then run this again.")