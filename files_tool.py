"""
File organization utilities. Sorts a folder's files into subfolders
by extension. Safe by default: only moves loose files, never deletes.
"""

import os
import shutil
import config

EXT_MAP = {
    "images": ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"],
    "documents": ["pdf", "docx", "doc", "txt", "md", "xlsx", "pptx", "csv"],
    "archives": ["zip", "rar", "7z", "tar", "gz"],
    "audio": ["mp3", "wav", "flac", "m4a"],
    "video": ["mp4", "mov", "avi", "mkv"],
    "installers": ["exe", "msi", "dmg", "pkg"],
    "code": ["py", "js", "html", "css", "json", "ipynb"],
}


def _category_for(ext: str) -> str:
    ext = ext.lower()
    for category, exts in EXT_MAP.items():
        if ext in exts:
            return category
    return "other"


def organize_folder(folder: str = None) -> str:
    folder = folder or config.DOWNLOADS_FOLDER
    if not os.path.isdir(folder):
        return f"Couldn't find folder: {folder}"

    moved = 0
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path):
            ext = f.split(".")[-1] if "." in f else "other"
            category = _category_for(ext)
            dest_dir = os.path.join(folder, category)
            os.makedirs(dest_dir, exist_ok=True)
            try:
                shutil.move(path, os.path.join(dest_dir, f))
                moved += 1
            except shutil.Error:
                pass  # file already exists at destination, skip

    return f"Organized {moved} file(s) in {folder} into category folders."


def create_folder(name: str, location: str = None) -> str:
    """Create a new folder, defaulting to Desktop if no location given."""
    location = location or config.DESKTOP_FOLDER
    path = os.path.join(location, name)
    try:
        if os.path.exists(path):
            return f"A folder called '{name}' already exists there."
        os.makedirs(path)
        return f"Created folder '{name}' on your Desktop."
    except Exception as e:
        return f"Couldn't create folder: {e}"


def create_file(name: str, location: str = None) -> str:
    """Create a new empty file, defaulting to Desktop and .txt if unspecified."""
    location = location or config.DESKTOP_FOLDER
    if "." not in name:
        name += ".txt"
    path = os.path.join(location, name)
    try:
        if os.path.exists(path):
            return f"A file called '{name}' already exists there."
        with open(path, "w") as f:
            pass
        return f"Created file '{name}' on your Desktop."
    except Exception as e:
        return f"Couldn't create file: {e}"


def find_and_delete(query: str, search_folders: list = None) -> str:
    """
    Search common locations for a file OR folder matching the query, and
    move it to the Recycle Bin (NEVER permanently delete). Requires
    `pip install send2trash`.
    """
    try:
        from send2trash import send2trash
    except ImportError:
        return "Safe delete needs one more package — run `pip install send2trash` first."

    if search_folders is None:
        search_folders = [
            config.DESKTOP_FOLDER,
            config.DOCUMENTS_FOLDER,
            config.DOWNLOADS_FOLDER,
        ]

    query_l = query.lower().strip()
    matches = []

    for base in search_folders:
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            for name in dirs + files:
                name_no_ext = os.path.splitext(name)[0].lower()
                if query_l == name_no_ext or query_l in name_no_ext or name_no_ext in query_l:
                    matches.append(os.path.join(root, name))
            if root.count(os.sep) - base.count(os.sep) >= 3:
                dirs[:] = []

    if not matches:
        return (f"Couldn't find anything matching '{query}' in Desktop, "
                f"Documents, or Downloads — nothing was deleted.")

    target = matches[0]
    try:
        send2trash(target)
        return (f"Moved '{os.path.basename(target)}' to the Recycle Bin — "
                f"you can restore it from there if this was a mistake.")
    except Exception as e:
        return f"Found it but couldn't delete it: {e}"


def find_duplicates(folder: str = None) -> list:
    """Find files with identical names+sizes (simple duplicate heuristic)."""
    folder = folder or config.DOWNLOADS_FOLDER
    seen = {}
    duplicates = []
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            key = (f, size)
            if key in seen:
                duplicates.append(path)
            else:
                seen[key] = path
    return duplicates