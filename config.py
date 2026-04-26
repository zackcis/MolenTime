"""Environment and paths for the Molengeek WakaTime leaderboard bot."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
STORAGE_IMAGES = ROOT / "storage" / "images"
DATA_DIR = ROOT / "data"

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
LEADERBOARD_CHANNEL_ID = int(os.getenv("LEADERBOARD_CHANNEL_ID", "0"))
WAKATIME_API_URL = os.getenv("WAKATIME_API_URL", "https://wakatime.com/api/v1").rstrip("/")
TIMEZONE = os.getenv("TIMEZONE", "Africa/Casablanca")
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "15"))
BUFFER_SLEEP_SECONDS = int(os.getenv("BUFFER_SLEEP_SECONDS", "60"))
ADMIN_USER_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_USER_IDS", "").split(",")
    if x.strip().isdigit()
}


def validate() -> str | None:
    if not DISCORD_BOT_TOKEN:
        return "DISCORD_BOT_TOKEN is missing in .env"
    if LEADERBOARD_CHANNEL_ID == 0:
        return "LEADERBOARD_CHANNEL_ID is missing or invalid in .env"
    return None


STORAGE_IMAGES.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
