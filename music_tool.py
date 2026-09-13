"""
Music control: play songs either from local files on your PC, or via
Spotify (if you've set up API credentials in config.py).

Local files: works immediately, no setup needed, just point
config.LOCAL_MUSIC_FOLDER at your music folder.

Spotify: needs one-time setup — see README for the steps.
"""

import os
import glob
import webbrowser
import urllib.parse
import config


# ---------------- Local file playback ----------------

def _find_local_song(query: str):
    """Search LOCAL_MUSIC_FOLDER for a filename that loosely matches the query."""
    query_l = query.lower()
    folder = config.LOCAL_MUSIC_FOLDER
    if not os.path.isdir(folder):
        return None

    matches = []
    for ext in ("mp3", "wav", "flac", "m4a"):
        matches.extend(glob.glob(os.path.join(folder, "**", f"*.{ext}"), recursive=True))

    for path in matches:
        name = os.path.splitext(os.path.basename(path))[0].lower()
        if query_l in name or name in query_l:
            return path
    return None


def play_local(query: str) -> str:
    path = _find_local_song(query)
    if not path:
        return f"Couldn't find a local song matching '{query}' in {config.LOCAL_MUSIC_FOLDER}."
    try:
        os.startfile(path)  # Windows: opens with your default music player
        return f"Playing '{os.path.basename(path)}' from your local music folder."
    except AttributeError:
        return "Local playback via os.startfile is Windows-only right now."
    except Exception as e:
        return f"Found the file but couldn't play it: {e}"


# ---------------- Spotify playback ----------------

_spotify_client = None


def _get_spotify_client():
    global _spotify_client
    if _spotify_client is not None:
        return _spotify_client

    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
    except ImportError:
        return None

    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        return None

    auth = SpotifyOAuth(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=".spotify_cache",
    )
    _spotify_client = spotipy.Spotify(auth_manager=auth)
    return _spotify_client


def play_spotify(query: str) -> str:
    sp = _get_spotify_client()
    if sp is None:
        return ("Spotify isn't set up yet — add SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET to config.py, and run "
                "`pip install spotipy` first. See README for the full steps.")

    try:
        results = sp.search(q=query, type="track", limit=1)
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            return f"Couldn't find '{query}' on Spotify."

        track = tracks[0]
        name = track["name"]
        artist = track["artists"][0]["name"]

        devices = sp.devices().get("devices", [])
        if not devices:
            return ("Found the song, but no active Spotify device. Open the "
                    "Spotify app on your PC or phone first, then try again.")

        sp.start_playback(device_id=devices[0]["id"], uris=[track["uri"]])
        return f"Playing '{name}' by {artist} on Spotify."
    except Exception as e:
        return f"Spotify playback failed: {e}"


def play_youtube_music(query: str) -> str:
    """
    Opens YouTube Music in your default browser, searching for the song.
    No API keys or setup needed — works immediately.

    Note: this isn't true remote-control playback like Spotify (YouTube
    Music has no public API for that). It opens a browser tab and starts
    playing there instead.
    """
    if not query.strip():
        return "What song do you want me to play on YouTube Music?"

    encoded_query = urllib.parse.quote(query)
    search_url = f"https://music.youtube.com/search?q={encoded_query}"

    try:
        webbrowser.open(search_url)
        return f"Opened YouTube Music and searched for '{query}' — click the top result to play it."
    except Exception as e:
        return f"Couldn't open the browser: {e}"


# ---------------- Combined entry point ----------------

def play_music(query: str, prefer: str = "auto") -> str:
    """
    prefer: 'local' | 'spotify' | 'youtube' | 'auto'
    'auto' tries local files first (instant, no internet needed),
    then falls back to Spotify if nothing local matches.
    """
    if prefer == "local":
        return play_local(query)
    if prefer == "spotify":
        return play_spotify(query)
    if prefer == "youtube":
        return play_youtube_music(query)

    local_result = play_local(query)
    if "Couldn't find" not in local_result:
        return local_result
    return play_spotify(query)