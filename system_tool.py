"""
System control and basic security-awareness utilities.
Only ever acts on THIS machine, and only on explicit command.
"""

import os
import platform
import subprocess
import psutil
import difflib
import json
import config
import re

IS_WINDOWS = platform.system() == "Windows"


def shutdown_pc():
    if IS_WINDOWS:
        os.system("shutdown /s /t 5")
    else:
        os.system("shutdown -h +0")
    return "Shutting down in 5 seconds. Say something to cancel... (Ctrl+C in this window)"


def restart_pc():
    if IS_WINDOWS:
        os.system("shutdown /r /t 5")
    else:
        os.system("shutdown -r +0")
    return "Restarting in 5 seconds."


def sleep_pc():
    if IS_WINDOWS:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Going to sleep."
    return "Sleep command isn't wired up for this OS yet."


def system_status() -> str:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return f"CPU: {cpu}% | Memory: {mem}% | Disk: {disk}%"


def security_scan() -> str:
    """Very basic anomaly check: flags unusually high CPU processes."""
    flags = []
    for p in psutil.process_iter(["name", "cpu_percent"]):
        try:
            if p.info["cpu_percent"] and p.info["cpu_percent"] > 50:
                flags.append(f"{p.info['name']} is using {p.info['cpu_percent']}% CPU")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not flags:
        return "Nothing unusual — no processes hogging resources right now."
    return "Heads up, found some high-usage processes:\n" + "\n".join(set(flags))


def _winget_find_id(query: str):
    """
    Search winget's ONLINE CATALOG for a package matching the query and
    return its exact ID (e.g. 'Valve.Steam') — used for INSTALLING new
    software.
    """
    try:
        result = subprocess.run(
            ["winget", "search", query, "--accept-source-agreements"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
        )
        lines = result.stdout.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("---"):
                if i + 1 < len(lines):
                    row = lines[i + 1]
                    parts = re.split(r"\s{2,}", row.strip())
                    if len(parts) >= 2:
                        return parts[1]  # the Id column
                break
    except Exception:
        pass
    return None


def _winget_find_installed_id(query: str):
    """
    Search what's ACTUALLY INSTALLED on this PC (winget list) for a
    match — used for UNINSTALLING. This is a different data source than
    the online catalog, since software installed outside of winget
    (e.g. Chrome downloaded directly from google.com) can be tracked
    under a different ID than what 'winget search' would suggest.
    """
    try:
        result = subprocess.run(
            ["winget", "list", query],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
        )
        lines = result.stdout.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("---"):
                if i + 1 < len(lines):
                    row = lines[i + 1]
                    parts = re.split(r"\s{2,}", row.strip())
                    if len(parts) >= 2:
                        return parts[1]  # the Id column
                break
    except Exception:
        pass
    return None


def install_app(app_name: str) -> str:
    """Install an app using Windows Package Manager (winget)."""
    exact_id = _winget_find_id(app_name)
    target = exact_id if exact_id else app_name
    try:
        args = ["winget", "install", "--accept-source-agreements", "--accept-package-agreements"]
        args += ["--id", target, "-e"] if exact_id else [target]
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if result.returncode == 0:
            return f"Installed {app_name} successfully."
        return f"Winget couldn't install '{app_name}'. Output: {result.stdout[-500:] or result.stderr[-500:]}"
    except FileNotFoundError:
        return "winget isn't available on this system — it comes with Windows 10/11 by default, check it's up to date."
    except subprocess.TimeoutExpired:
        return "Install timed out — it might still be running in the background, check manually."
    except Exception as e:
        return f"Install failed: {e}"


def uninstall_app(app_name: str) -> str:
    """Uninstall an app using Windows Package Manager (winget)."""
    exact_id = _winget_find_installed_id(app_name)
    target = exact_id if exact_id else app_name
    try:
        args = ["winget", "uninstall", "--accept-source-agreements"]
        args += ["--id", target, "-e"] if exact_id else [target]
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        if result.returncode == 0:
            return f"Uninstalled {app_name} successfully."
        return (f"Winget couldn't uninstall '{app_name}' — some apps with their own "
                f"auto-updater (like Chrome) don't always play nice with winget. "
                f"Try saying 'open add or remove programs' and removing it from there instead.")
    except FileNotFoundError:
        return "winget isn't available on this system."
    except subprocess.TimeoutExpired:
        return "Uninstall timed out — check manually if it went through."
    except Exception as e:
        return f"Uninstall failed: {e}"


def _get_all_start_apps():
    """
    Get every app Windows knows about — both traditional desktop apps
    AND Microsoft Store apps (like Amazon Music, Spotify from Store, etc.)
    using PowerShell's Get-StartApps, which is the same list Windows
    Search uses internally.
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-StartApps | ConvertTo-Json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        if isinstance(data, dict):  # only one app returned, not a list
            data = [data]
        return {item["Name"].lower(): item["AppID"] for item in data
                if "Name" in item and "AppID" in item}
    except Exception:
        return {}


def _find_app_id(query: str):
    apps = _get_all_start_apps()
    if not apps:
        return None

    query_l = query.lower().strip()

    # exact or substring match first
    for name, app_id in apps.items():
        if query_l == name or query_l in name or name in query_l:
            return app_id

    # fuzzy fallback for typos/close names
    close = difflib.get_close_matches(query_l, apps.keys(), n=1, cutoff=0.6)
    if close:
        return apps[close[0]]

    return None


def find_and_open_folder(query: str, search_folders: list = None) -> str:
    """
    Search common locations (Desktop, Documents, Downloads, and your user
    home folder) for a FOLDER whose name loosely matches the query, and
    open it in File Explorer.
    """
    if search_folders is None:
        search_folders = [
            os.path.expanduser("~"),
            config.DESKTOP_FOLDER,
            config.DOCUMENTS_FOLDER,
            config.DOWNLOADS_FOLDER,
        ]

    query_l = query.lower().strip()
    matches = []
    all_dirs = {}

    for base in search_folders:
        if not os.path.isdir(base):
            continue
        for root, dirs, _ in os.walk(base):
            for d in dirs:
                name_l = d.lower()
                all_dirs[name_l] = os.path.join(root, d)
                if query_l == name_l or query_l in name_l or name_l in query_l:
                    matches.append(os.path.join(root, d))
            # don't descend too deep — keeps this fast
            if root.count(os.sep) - base.count(os.sep) >= 3:
                dirs[:] = []

    if not matches:
        close = difflib.get_close_matches(query_l, all_dirs.keys(), n=1, cutoff=0.5)
        if close:
            matches = [all_dirs[close[0]]]

    if not matches:
        return (f"Couldn't find a folder matching '{query}' in your Desktop, "
                f"Documents, Downloads, or user folder.")

    try:
        os.startfile(matches[0])
        return f"Opening the '{os.path.basename(matches[0])}' folder."
    except Exception as e:
        return f"Found the folder but couldn't open it: {e}"


def find_and_open_file(query: str, search_folders: list = None) -> str:
    """
    Search common folders (Desktop, Documents, Downloads by default) for a
    file whose name loosely matches the query, and open it with whatever
    program is set as default for that file type.
    """
    if search_folders is None:
        search_folders = [
            config.DESKTOP_FOLDER,
            config.DOCUMENTS_FOLDER,
            config.DOWNLOADS_FOLDER,
        ]

    query_l = query.lower().strip()
    matches = []

    for folder in search_folders:
        if not os.path.isdir(folder):
            continue
        for root, _, files in os.walk(folder):
            for f in files:
                name_no_ext = os.path.splitext(f)[0].lower()
                if query_l in name_no_ext or name_no_ext in query_l:
                    matches.append(os.path.join(root, f))

    if not matches:
        # fuzzy fallback
        all_files = {}
        for folder in search_folders:
            if not os.path.isdir(folder):
                continue
            for root, _, files in os.walk(folder):
                for f in files:
                    all_files[os.path.splitext(f)[0].lower()] = os.path.join(root, f)
        close = difflib.get_close_matches(query_l, all_files.keys(), n=1, cutoff=0.5)
        if close:
            matches = [all_files[close[0]]]

    if not matches:
        return (f"Couldn't find a file matching '{query}' in Desktop, "
                f"Documents, or Downloads.")

    try:
        os.startfile(matches[0])
        return f"Opening '{os.path.basename(matches[0])}'."
    except Exception as e:
        return f"Found the file but couldn't open it: {e}"


def open_app(app_name: str) -> str:
    """
    Open an application. Tries these in order:
    1. A small manual list for special cases that aren't real apps
       (URLs, OS panels like Settings/Task Manager).
    2. Searching ALL apps Windows knows about (desktop + Microsoft Store)
       via Get-StartApps — this covers virtually everything automatically.
    3. Trying the raw name directly as a last resort.
    """
    special_cases = {
        "copilot": "https://copilot.microsoft.com",
        "settings": "ms-settings:",
        "task manager": "taskmgr",
        "terminal": "wt",
        "add or remove programs": "ms-settings:appsfeatures",
        "uninstall programs": "ms-settings:appsfeatures",
        "app list": "ms-settings:appsfeatures",
    }

    key = app_name.lower().strip()

    if key in special_cases:
        cmd = special_cases[key]
        os.system(f"start {cmd}" if IS_WINDOWS else f"open -a '{cmd}'")
        return f"Opening {app_name}."

    if IS_WINDOWS:
        app_id = _find_app_id(key)
        if app_id:
            try:
                os.system(f'explorer.exe shell:AppsFolder\\{app_id}')
                return f"Opening {app_name}."
            except Exception as e:
                return f"Found {app_name} but couldn't launch it: {e}"

    # last resort: try the raw name directly
    try:
        cmd = key.replace(" ", "")
        os.system(f"start {cmd}" if IS_WINDOWS else f"open -a '{cmd}'")
        return f"Trying to open {app_name}."
    except Exception as e:
        return f"Couldn't find or open '{app_name}': {e}"