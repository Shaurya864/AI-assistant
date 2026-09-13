"""
Central configuration for your local assistant.
Edit this file to change its personality, models, and behavior.
"""

# ---- Personality ----
SYSTEM_PROMPT = """You are JARVIS, a witty, concise, and helpful personal AI assistant
running locally on the user's own computer. Keep responses natural and conversational,
not overly long unless asked for detail. You can be a little dry/sarcastic, but always
genuinely helpful. Address the user as 'sir' or 'boss' only occasionally, not every line."""

# ---- Models (must be pulled via `ollama pull <name>` first) ----
GENERAL_MODEL = "llama3.1:8b"
CODE_MODEL = "qwen2.5-coder"
MATH_MODEL = "llama3.1:8b"  # sympy handles the actual computation; LLM explains it

# ---- Ollama connection ----
OLLAMA_URL = "http://localhost:11434/api/generate"

# ---- Voice ----
VOICE_ENABLED = False        # legacy flag, no longer needed — just say "listen" anytime to use voice for one turn
WAKE_WORD = "jarvis"         # only used if you add a wake-word listener later

# Whisper (speech-to-text) settings
# Model sizes, from fastest/least accurate to slowest/most accurate:
# tiny.en < base.en < small.en < medium.en < large-v3
WHISPER_MODEL = "medium.en"
WHISPER_DEVICE = "cuda"   # uses your RTX 3050; falls back to CPU automatically if unavailable
LISTEN_DURATION = 5       # seconds of mic recording per request

# Paths for Piper text-to-speech — point these at wherever you placed
# the piper folder and voice model files (see README voice setup steps)
import os as _os
PROJECT_DIR = _os.path.dirname(_os.path.abspath(__file__))
PIPER_EXE_PATH = _os.path.join(PROJECT_DIR, "piper", "piper.exe")
PIPER_VOICE_PATH = _os.path.join(PROJECT_DIR, "en_US-lessac-medium.onnx")

# ---- Known folder resolution (handles OneDrive redirection correctly) ----
def get_known_folder(name: str) -> str:
    """
    Get the REAL path for Desktop/Documents/Downloads. On many PCs (like
    this one), OneDrive redirects these folders to live inside the
    OneDrive folder instead of their plain default location — this reads
    the actual redirected path from the Windows registry so every feature
    (create/open/delete files) agrees on where your real folders are.
    """
    import platform
    if platform.system() != "Windows":
        return _os.path.join(_os.path.expanduser("~"), name)
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        folder_ids = {
            "Desktop": "Desktop",
            "Documents": "Personal",
            "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
        }
        value_name = folder_ids.get(name, name)
        path, _ = winreg.QueryValueEx(key, value_name)
        return _os.path.expandvars(path)
    except Exception:
        return _os.path.join(_os.path.expanduser("~"), name)


# ---- Folders ----
DOWNLOADS_FOLDER = get_known_folder("Downloads")
DESKTOP_FOLDER = get_known_folder("Desktop")
DOCUMENTS_FOLDER = get_known_folder("Documents")

# ---- Music ----
# Local music: point this at the folder where your songs are stored
LOCAL_MUSIC_FOLDER = _os.path.expanduser("~/Music")

# Spotify: get these from https://developer.spotify.com/dashboard
# (create an app there, it gives you a Client ID and Client Secret)
SPOTIFY_CLIENT_ID = ""       # paste your Client ID here
SPOTIFY_CLIENT_SECRET = ""   # paste your Client Secret here
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# ---- RAG Memory ----
# Drop .txt or .md files here that you want Jarvis to actually know about
# (notes, project docs, reference material, etc.)
KNOWLEDGE_FOLDER = _os.path.join(PROJECT_DIR, "knowledge")
EMBEDDING_MODEL = "nomic-embed-text"  # pull via: ollama pull nomic-embed-text

# ---- Weather ----
# Set your city here for quick "weather" requests (leave blank to
# auto-detect your location from your IP instead)
WEATHER_LOCATION = ""

# ---- News ----
NEWS_RSS_FEEDS = {
    "top": "http://feeds.bbci.co.uk/news/rss.xml",
    "tech": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "sports": "http://feeds.bbci.co.uk/sport/rss.xml",
}

# ---- Safety ----
# Commands the assistant will NEVER execute, even if asked, as a basic safety net
# on top of good judgement in main.py
BLOCKED_KEYWORDS = ["format c:", "rm -rf /", "del /f /s /q c:\\"]