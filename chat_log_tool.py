"""
Full conversation history logging. Every exchange gets silently appended
to chat_history.jsonl in your project folder — nothing extra needed,
this happens automatically in the background.

You can then ask "show chat history" or "search history for [topic]"
to look back at past conversations.
"""

import json
import os
from datetime import datetime
import config

LOG_PATH = os.path.join(config.PROJECT_DIR, "chat_history.jsonl")


def log_exchange(user_text: str, response_text: str):
    """Append one exchange to the history log. Silently does nothing on failure —
    logging should never be able to break the actual conversation."""
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user": user_text,
        "assistant": response_text,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def get_recent_history(n: int = 10) -> str:
    """Show the last n exchanges."""
    if not os.path.isfile(LOG_PATH):
        return "No chat history yet."

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return f"Couldn't read history: {e}"

    recent = lines[-n:]
    if not recent:
        return "No chat history yet."

    formatted = []
    for line in recent:
        try:
            entry = json.loads(line)
            ts = entry["timestamp"].replace("T", " ")
            reply_preview = entry["assistant"][:150]
            formatted.append(f"[{ts}] You: {entry['user']}\n  Jarvis: {reply_preview}")
        except Exception:
            continue

    return "Recent conversation history:\n\n" + "\n\n".join(formatted)


def prune_old_history(days: int = 30):
    """
    Automatically move chat entries older than `days` days to the Recycle
    Bin, keeping only recent history in the active log. Call this once
    at startup — runs silently, returns None if nothing needed pruning.
    """
    if not os.path.isfile(LOG_PATH):
        return None

    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    recent_lines, old_lines = [], []

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    (recent_lines if entry_time >= cutoff else old_lines).append(line)
                except Exception:
                    recent_lines.append(line)  # keep anything unparseable, never lose data by mistake
    except Exception:
        return None

    if not old_lines:
        return None  # nothing old enough to prune

    try:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.writelines(recent_lines)
    except Exception:
        return None

    # Archive the pruned entries to their own file, then send THAT to the
    # Recycle Bin — recoverable if you ever need old chats back
    archive_name = f"chat_history_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    archive_path = os.path.join(config.PROJECT_DIR, archive_name)
    try:
        with open(archive_path, "w", encoding="utf-8") as f:
            f.writelines(old_lines)
        from send2trash import send2trash
        send2trash(archive_path)
        return f"Auto-cleaned {len(old_lines)} chat entries older than {days} days (moved to Recycle Bin)."
    except ImportError:
        return f"Found {len(old_lines)} old chat entries but couldn't archive them — run `pip install send2trash`."
    except Exception:
        return None


def clear_history() -> str:
    """Move the chat history file to the Recycle Bin — recoverable, never permanent."""
    if not os.path.isfile(LOG_PATH):
        return "There's no chat history to clear yet."

    try:
        from send2trash import send2trash
        send2trash(LOG_PATH)
        return "Chat history moved to the Recycle Bin — you can restore it from there if needed."
    except ImportError:
        return "Clearing history safely needs one more package — run `pip install send2trash` first."
    except Exception as e:
        return f"Couldn't clear history: {e}"


def search_history(query: str) -> str:
    """Search all past conversations for a keyword or topic."""
    if not os.path.isfile(LOG_PATH):
        return "No chat history yet."

    query_l = query.lower().strip()
    matches = []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if query_l in entry["user"].lower() or query_l in entry["assistant"].lower():
                        ts = entry["timestamp"].replace("T", " ")
                        reply_preview = entry["assistant"][:150]
                        matches.append(f"[{ts}] You: {entry['user']}\n  Jarvis: {reply_preview}")
                except Exception:
                    continue
    except Exception as e:
        return f"Couldn't search history: {e}"

    if not matches:
        return f"Nothing found matching '{query}' in our chat history."

    # Cap output so a broad search doesn't dump your whole history
    shown = matches[-10:]
    header = f"Found {len(matches)} match(es)"
    if len(matches) > 10:
        header += " (showing the 10 most recent)"
    return f"{header}:\n\n" + "\n\n".join(shown)