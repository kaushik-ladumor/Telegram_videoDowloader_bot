import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")


async def create_download_link(file_path: str, file_name: str) -> str:
    """
    Tell Node.js server about the downloaded file.
    Node.js creates a token and returns a download URL.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/create-link",
            json={
                "filePath": file_path,
                "fileName": file_name,
            },
            timeout=10
        )

        data = response.json()

        if response.status_code == 200 and data.get("url"):
            return data["url"]
        else:
            raise Exception(data.get("error", "Failed to create download link"))

    except requests.exceptions.ConnectionError:
        raise Exception("Download server is not running. Start Node.js server first.")
    except Exception as e:
        raise Exception(f"Server error: {str(e)}")