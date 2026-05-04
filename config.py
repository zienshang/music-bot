import os
from dotenv import load_dotenv

load_dotenv()

# 🔐 BOT TOKEN
TOKEN = os.getenv("TOKEN")

# 🎧 PREFIX COMMAND
PREFIX = "-"

# 💿 LAVALINK CONFIG
LAVALINK_URI = os.getenv("LAVALINK_URI", "http://127.0.0.1:2333")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

# 🔊 DEFAULT VOLUME (LAVALINK)
DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", 50))

# 🎵 SPOTIFY (optional)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
