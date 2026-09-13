"""
JARVIS HUD - a small always-on-top arc-reactor style overlay window.

Shows three states:
  idle      - slow calm breathing pulse (default / listening for wake input)
  listening - faster pulse + spinning rings (mic actively recording)
  speaking  - fast pulse + waveform bars (Jarvis talking)

Usage from main.py:

    import threading
    import hud

    def run_console():
        main()  # your existing console loop

    if __name__ == "__main__":
        threading.Thread(target=run_console, daemon=True).start()
        hud.launch()   # blocks - must run on the main thread

Then anywhere you want the HUD to react:

    hud.set_state("listening")
    text = listen()
    hud.set_state("idle")

    hud.set_state("speaking")
    speak(response)
    hud.set_state("idle")

If the HUD window hasn't been launched (e.g. you're testing in a plain
console), set_state() is a harmless no-op.
"""

import sys
import threading
import ctypes

_window = None
_lock = threading.Lock()

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {
    margin: 0; padding: 0; width: 100%; height: 100%;
    background: transparent;
    overflow: hidden;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    -webkit-user-select: none;
    user-select: none;
  }
  body {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh;
  }
  #hudRoot {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    transform: scale(__SCALE__);
  }
  #stage {
    position: relative;
    width: 340px; height: 340px;
  }
  #aura {
    position: absolute; top: 50%; left: 50%;
    width: 480px; height: 480px;
    transform: translate(-50%, -50%) scale(1);
    border-radius: 50%;
    background: radial-gradient(circle, rgba(45,212,232,0.16) 0%, rgba(45,212,232,0.05) 45%, rgba(45,212,232,0) 72%);
    transition: opacity 0.6s ease;
    animation: auraBreathe 4.5s ease-in-out infinite;
  }
  #rings { position: absolute; top: 0; left: 0; }
  #core {
    position: absolute;
    top: 95px; left: 95px;
    width: 150px; height: 150px;
    border-radius: 50%;
    background: radial-gradient(circle at 42% 40%,
      #ffffff 0%, #baf6ff 12%, #5fe0ee 30%, #17a6bd 52%, #0a4650 74%, #051d22 100%);
    box-shadow:
      0 0 8px 2px rgba(255,255,255,0.5),
      0 0 45px 12px rgba(45,212,232,0.55),
      0 0 100px 34px rgba(45,212,232,0.22);
    display: flex; align-items: center; justify-content: center;
    transition: box-shadow 0.5s ease;
  }
  #coreRim {
    position: absolute; top: -4px; left: -4px;
    width: 158px; height: 158px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.35);
  }
  #coreDot {
    width: 46px; height: 46px; border-radius: 50%;
    background: radial-gradient(circle, #ffffff 0%, #cffcff 60%, #7fe9f2 100%);
    box-shadow: 0 0 24px 8px rgba(255,255,255,0.85);
    animation: flicker 2.6s ease-in-out infinite;
  }
  #sweep {
    position: absolute; top: 0; left: 0;
    width: 340px; height: 340px;
    border-radius: 50%;
    background: conic-gradient(from 0deg, rgba(45,212,232,0.28), rgba(45,212,232,0) 24%);
    animation: spinSlow 4s linear infinite;
    opacity: 0.7;
  }
  #particles { position: absolute; top: 0; left: 0; width: 340px; height: 340px; }
  .particle {
    position: absolute; width: 4px; height: 4px; border-radius: 50%;
    background: #baf6ff; box-shadow: 0 0 6px 2px rgba(186,246,255,0.8);
  }
  .bracket {
    position: absolute; width: 28px; height: 28px;
    border: 1.5px solid rgba(45,212,232,0.55);
    opacity: 0.8;
  }
  #bTL { top: -18px; left: -18px; border-right: none; border-bottom: none; }
  #bTR { top: -18px; right: -18px; border-left: none; border-bottom: none; }
  #bBL { bottom: -18px; left: -18px; border-right: none; border-top: none; }
  #bBR { bottom: -18px; right: -18px; border-left: none; border-top: none; }
  #waveWrap {
    display: flex; align-items: flex-end; justify-content: center;
    gap: 5px; height: 30px; margin-top: 26px;
    opacity: 0; transition: opacity 0.3s ease;
  }
  .wbar {
    width: 4px; background: linear-gradient(#baf6ff, #2dd4e8); border-radius: 2px;
    animation: wave 0.9s ease-in-out infinite;
  }
  @keyframes wave { 0%, 100% { height: 6px; } 50% { height: 28px; } }
  @keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  @keyframes spinRev  { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
  @keyframes pulseIdle   { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.035); } }
  @keyframes pulseListen { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.09); } }
  @keyframes auraBreathe { 0%, 100% { opacity: 0.55; } 50% { opacity: 1; } }
  @keyframes flicker { 0%, 100% { opacity: 1; } 48% { opacity: 0.85; } 50% { opacity: 1; } 51% { opacity: 0.9; } }
  @keyframes orbit {
    from { transform: rotate(0deg) translateX(var(--orbit-r)) rotate(0deg); }
    to   { transform: rotate(360deg) translateX(var(--orbit-r)) rotate(-360deg); }
  }
  #label {
    text-align: center; color: #7fe9f2; font-size: 12px; font-weight: 600;
    letter-spacing: 4px; text-transform: uppercase;
    margin-top: 10px; opacity: 0.85;
    text-shadow: 0 0 12px rgba(45,212,232,0.6);
  }
</style>
</head>
<body>
<div id="hudRoot">
<div id="stage">
  <div id="aura"></div>
  <svg id="rings" width="340" height="340" viewBox="0 0 340 340">
    <circle cx="170" cy="170" r="164" fill="none" stroke="#123b45" stroke-width="0.75" opacity="0.5"/>
    <circle id="ringFar" cx="170" cy="170" r="148" fill="none" stroke="#2dd4e8" stroke-width="0.75" stroke-dasharray="1 14" opacity="0.4"/>
    <circle id="ringOuter" cx="170" cy="170" r="128" fill="none" stroke="#2dd4e8" stroke-width="1.5" stroke-dasharray="8 12" opacity="0.65"/>
    <circle id="ringMid" cx="170" cy="170" r="104" fill="none" stroke="#2dd4e8" stroke-width="1" stroke-dasharray="3 7" opacity="0.45"/>
    <circle id="ringInner" cx="170" cy="170" r="86" fill="none" stroke="#baf6ff" stroke-width="0.75" stroke-dasharray="2 4" opacity="0.35"/>
    <g id="ticks"></g>
  </svg>
  <div id="sweep"></div>
  <div id="particles"></div>
  <div id="core">
    <div id="coreRim"></div>
    <div id="coreDot"></div>
  </div>
  <div id="bTL" class="bracket"></div>
  <div id="bTR" class="bracket"></div>
  <div id="bBL" class="bracket"></div>
  <div id="bBR" class="bracket"></div>
</div>
<div id="waveWrap"></div>
<div id="label">idle</div>
</div>

<script>
const core = document.getElementById('core');
const aura = document.getElementById('aura');
const sweep = document.getElementById('sweep');
const ringFar = document.getElementById('ringFar');
const ringOuter = document.getElementById('ringOuter');
const ringMid = document.getElementById('ringMid');
const ringInner = document.getElementById('ringInner');
const waveWrap = document.getElementById('waveWrap');
const ticks = document.getElementById('ticks');
const particles = document.getElementById('particles');
const label = document.getElementById('label');

const cx = 170, cy = 170, r = 164;
for (let i = 0; i < 36; i++) {
  const a = (i / 36) * 2 * Math.PI;
  const major = i % 3 === 0;
  const len = major ? 10 : 5;
  const x1 = cx + Math.cos(a) * r, y1 = cy + Math.sin(a) * r;
  const x2 = cx + Math.cos(a) * (r - len), y2 = cy + Math.sin(a) * (r - len);
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', x1); line.setAttribute('y1', y1);
  line.setAttribute('x2', x2); line.setAttribute('y2', y2);
  line.setAttribute('stroke', major ? '#2dd4e8' : '#1c5560');
  line.setAttribute('stroke-width', major ? '1.2' : '0.75');
  line.setAttribute('opacity', major ? '0.7' : '0.4');
  ticks.appendChild(line);
}
for (let i = 0; i < 5; i++) {
  const bar = document.createElement('div');
  bar.className = 'wbar';
  bar.style.animationDelay = (i * 0.12) + 's';
  waveWrap.appendChild(bar);
}
const orbitRadii = [150, 118];
for (let i = 0; i < 6; i++) {
  const p = document.createElement('div');
  p.className = 'particle';
  const rOrb = orbitRadii[i % 2];
  p.style.setProperty('--orbit-r', rOrb + 'px');
  p.style.top = '170px';
  p.style.left = '170px';
  p.style.marginLeft = '-2px';
  p.style.marginTop = '-2px';
  const dur = 10 + i * 3;
  const dir = i % 2 === 0 ? 'normal' : 'reverse';
  p.style.animation = 'orbit ' + dur + 's linear infinite ' + dir;
  p.style.animationDelay = (-i * 1.7) + 's';
  particles.appendChild(p);
}

ringFar.style.transformOrigin = '170px 170px';
ringOuter.style.transformOrigin = '170px 170px';
ringMid.style.transformOrigin = '170px 170px';
ringInner.style.transformOrigin = '170px 170px';
ringFar.style.animation = 'spinRev 40s linear infinite';
ringOuter.style.animation = 'spinSlow 22s linear infinite';
ringMid.style.animation = 'spinRev 28s linear infinite';
ringInner.style.animation = 'spinSlow 16s linear infinite';

function setState(state) {
  if (state === 'idle') {
    core.style.animation = 'pulseIdle 3s ease-in-out infinite';
    core.style.boxShadow = '0 0 8px 2px rgba(255,255,255,0.4), 0 0 45px 12px rgba(45,212,232,0.45), 0 0 100px 34px rgba(45,212,232,0.18)';
    sweep.style.animationDuration = '7s';
    aura.style.animationDuration = '4.5s';
    waveWrap.style.opacity = '0';
    label.textContent = 'idle';
  } else if (state === 'listening') {
    core.style.animation = 'pulseListen 1.1s ease-in-out infinite';
    core.style.boxShadow = '0 0 10px 3px rgba(255,255,255,0.55), 0 0 60px 18px rgba(45,212,232,0.65), 0 0 130px 44px rgba(45,212,232,0.3)';
    sweep.style.animationDuration = '2.2s';
    aura.style.animationDuration = '1.6s';
    waveWrap.style.opacity = '0';
    label.textContent = 'listening';
  } else if (state === 'speaking') {
    core.style.animation = 'pulseListen 0.5s ease-in-out infinite';
    core.style.boxShadow = '0 0 12px 4px rgba(255,255,255,0.7), 0 0 70px 20px rgba(186,246,255,0.75), 0 0 140px 48px rgba(45,212,232,0.35)';
    sweep.style.animationDuration = '1.1s';
    aura.style.animationDuration = '0.9s';
    waveWrap.style.opacity = '1';
    label.textContent = 'speaking';
  } else if (state === 'thinking') {
    core.style.animation = 'pulseListen 1.6s ease-in-out infinite';
    core.style.boxShadow = '0 0 8px 2px rgba(230,220,255,0.5), 0 0 50px 14px rgba(122,90,248,0.55), 0 0 110px 36px rgba(122,90,248,0.22)';
    sweep.style.animationDuration = '3.4s';
    aura.style.animationDuration = '2.6s';
    waveWrap.style.opacity = '0';
    label.textContent = 'thinking';
  }
}
setState('idle');
</script>
</body>
</html>
"""

VALID_STATES = ("idle", "listening", "speaking", "thinking")


def _get_screen_size():
    """Best-effort screen resolution, Windows-first since that's the target."""
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            pass
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return w, h
    except Exception:
        return 1920, 1080


def _find_own_hwnd(target_width: int, target_height: int):
    """
    Find our own top-level window reliably. FindWindowW(None, title) is
    brittle - frameless webview windows don't always expose the exact
    title string for an exact match, and a silent miss there means
    click-through never gets applied with no error shown anywhere.
    Instead: enumerate every visible top-level window owned by THIS
    process, and pick the one whose size matches what we created
    (closest match wins - there's normally only one candidate anyway).
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = kernel32.GetCurrentProcessId()
    candidates = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        owner_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
        if owner_pid.value != pid:
            return True
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w > 0 and h > 0:
            candidates.append((hwnd, w, h))
        return True

    user32.EnumWindows(_enum, 0)
    if not candidates:
        return None

    candidates.sort(key=lambda t: abs(t[1] - target_width) + abs(t[2] - target_height))
    return candidates[0][0]


def _make_click_through(target_width: int, target_height: int) -> bool:
    """
    Windows only: lets clicks pass through the window to whatever's
    underneath, so a full-screen HUD doesn't block you from using your
    PC. Returns True/False so the caller can tell (and print) whether
    it actually worked instead of failing silently.
    """
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = _find_own_hwnd(target_width, target_height)
        if not hwnd:
            return False
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        # Re-check it actually stuck.
        new_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        return bool(new_style & WS_EX_TRANSPARENT)
    except Exception:
        return False


def _register_emergency_hotkey():
    """
    Safety net independent of click-through working at all: a global
    hotkey (Ctrl+Alt+H) that hides/shows the HUD instantly, regardless
    of whether the window is currently blocking clicks. Requires the
    optional 'keyboard' package - if it's not installed, this just
    quietly does nothing and you fall back to Task Manager if needed.
    """
    try:
        import keyboard
    except ImportError:
        print("[hud] Tip: `pip install keyboard` to enable the Ctrl+Alt+H "
              "emergency show/hide hotkey.")
        return

    state = {"visible": True}

    def _toggle():
        if _window is None:
            return
        try:
            if state["visible"]:
                _window.hide()
            else:
                _window.show()
            state["visible"] = not state["visible"]
        except Exception:
            pass

    keyboard.add_hotkey("ctrl+alt+h", _toggle)
    print("[hud] Emergency hotkey armed: Ctrl+Alt+H hides/shows the HUD instantly.")


def launch(fullscreen: bool = False, click_through: bool = None,
           width: int = 300, height: int = 340, x: int = None, y: int = None,
           corner: str = "bottom-right", margin: int = 24):
    """
    Create and run the HUD window. This BLOCKS, so call it from your
    main thread and run the rest of Jarvis (the console/voice loop) on
    a background thread instead. See module docstring for the pattern.

    fullscreen    - if True, sizes the window to your full screen and
                     centers the reactor in it. Default False: a small,
                     draggable corner widget instead (`width`/`height`).
    click_through - if None (default), automatically True when
                     fullscreen (so it never blocks your screen) and
                     False otherwise (so you can drag the small widget
                     around). Pass True/False explicitly to override.
    corner        - where the small widget starts: "bottom-right"
                     (default), "bottom-left", "top-right", "top-left".
                     Ignored if `x`/`y` are given, or if fullscreen.
    margin        - pixel gap from the screen edge for `corner`.
    """
    import webview

    global _window

    if click_through is None:
        click_through = fullscreen

    if fullscreen:
        width, height = _get_screen_size()
        x, y = 0, 0
    elif x is None and y is None:
        screen_w, screen_h = _get_screen_size()
        positions = {
            "bottom-right": (screen_w - width - margin, screen_h - height - margin),
            "bottom-left": (margin, screen_h - height - margin),
            "top-right": (screen_w - width - margin, margin),
            "top-left": (margin, margin),
        }
        x, y = positions.get(corner, positions["bottom-right"])

    # The reactor was designed at a 400x460 baseline. When the window is
    # smaller than that, scale the whole thing down to fit instead of
    # cropping it - keeps every ring/particle/bracket proportional.
    BASE_W, BASE_H = 400, 460
    scale = min(width / BASE_W, height / BASE_H, 1.0)
    scale = max(scale, 0.3)
    page_html = HTML.replace("__SCALE__", f"{scale:.4f}")

    kwargs = dict(
        title="JARVIS",
        html=page_html,
        width=width,
        height=height,
        frameless=True,
        easy_drag=not click_through,
        on_top=True,
        transparent=True,
        background_color="#000000",
    )
    if x is not None and y is not None:
        kwargs["x"] = x
        kwargs["y"] = y

    _window = webview.create_window(**kwargs)

    def _on_loaded():
        if click_through:
            ok = _make_click_through(width, height)
            if ok:
                print("[hud] Click-through enabled - the HUD won't block clicks.")
            else:
                print("[hud] WARNING: click-through failed to apply. The HUD "
                      "may be blocking clicks on screen right now. Press "
                      "Ctrl+Alt+H (if the 'keyboard' package is installed) "
                      "or use Task Manager to end python.exe.")
        _register_emergency_hotkey()

    _window.events.loaded += _on_loaded

    webview.start()


def set_state(state: str):
    """
    Push a state to the HUD ('idle' | 'listening' | 'speaking' | 'thinking').
    Safe to call even if the HUD window isn't running - it just no-ops.
    """
    if state not in VALID_STATES:
        return
    with _lock:
        if _window is None:
            return
        try:
            _window.evaluate_js(f"setState('{state}')")
        except Exception:
            # window not ready yet / already closed - ignore, HUD is cosmetic
            pass


def hide():
    """Manually hide the HUD window (e.g. bind this to your own hotkey)."""
    if _window is not None:
        try:
            _window.hide()
        except Exception:
            pass


def show():
    """Manually show the HUD window again after hide()."""
    if _window is not None:
        try:
            _window.show()
        except Exception:
            pass


def close():
    """Close the HUD window entirely."""
    if _window is not None:
        try:
            _window.destroy()
        except Exception:
            pass