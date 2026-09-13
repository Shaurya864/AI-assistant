"""
Screen splitting / window snapping, using Windows' built-in Snap feature
(the same thing that happens when you drag a window to the edge of your
screen, or press Win+Left/Win+Right yourself).

Requires: pip install pyautogui
"""

import time

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


def _check_available() -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Screen splitting needs one more package — run `pip install pyautogui` first."
    return None


def snap_left() -> str:
    """Snap the currently focused window to the left half of the screen."""
    err = _check_available()
    if err:
        return err
    pyautogui.hotkey('win', 'left')
    return "Snapped the active window to the left half."


def snap_right() -> str:
    """Snap the currently focused window to the right half of the screen."""
    err = _check_available()
    if err:
        return err
    pyautogui.hotkey('win', 'right')
    return "Snapped the active window to the right half."


def split_screen(app1: str, app2: str) -> str:
    """
    Open two apps and snap them side by side: app1 on the left,
    app2 on the right. Uses system_tool.open_app to launch each.
    """
    err = _check_available()
    if err:
        return err

    from system_tool import open_app

    open_app(app1)
    time.sleep(2.5)  # give it time to actually open and gain focus
    pyautogui.hotkey('win', 'left')
    time.sleep(0.7)

    open_app(app2)
    time.sleep(2.5)
    pyautogui.hotkey('win', 'right')

    return f"Split screen set up: {app1} on the left, {app2} on the right."
