import subprocess
import platform
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

from core.project import get_active_project
from core.logger import slugify_note

OS = platform.system()

# ── screenshot modes ─────────────────────────────────────────
MODE_FULL       = "full"       # entire screen, no interaction
MODE_ANNOTATE   = "annotate"   # flameshot gui — user draws, highlights
MODE_NONE       = "none"       # no screenshot

# ── main capture function ────────────────────────────────────
def capture(
    note      : str,
    category  : str,
    mode      : str = MODE_ANNOTATE,
    on_done   : Optional[Callable[[str], None]] = None,
) -> None:
    if mode == MODE_NONE:
        if on_done:
            on_done(None)
        return

    project_path = get_active_project()
    if not project_path:
        if on_done:
            on_done(None)
        return

    screenshots_dir = project_path / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    filename = slugify_note(note, category) + ".png"
    out_path = screenshots_dir / filename

    # run in thread so UI never blocks
    thread = threading.Thread(
        target=_run_capture,
        args=(mode, out_path, on_done),
        daemon=True,
    )
    thread.start()

# ── capture router ───────────────────────────────────────────
def _run_capture(
    mode     : str,
    out_path : Path,
    on_done  : Optional[Callable[[str], None]],
) -> None:
    success = False

    if OS == "Linux":
        success = _linux_capture(mode, out_path)
    elif OS == "Darwin":
        success = _mac_capture(mode, out_path)
    elif OS == "Windows":
        success = _windows_capture(out_path)

    result = str(out_path) if success and out_path.exists() else None

    if on_done:
        on_done(result)

# ── linux ────────────────────────────────────────────────────
def _linux_capture(mode: str, out_path: Path) -> bool:
    if _flameshot_available():
        return _flameshot(mode, out_path)
    return _pyautogui_capture(out_path)

def _flameshot_available() -> bool:
    try:
        result = subprocess.run(
            ["which", "flameshot"],
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False

def _flameshot(mode: str, out_path: Path) -> bool:
    try:
        if mode == MODE_ANNOTATE:
            cmd = ["flameshot", "gui", "--path", str(out_path)]
        else:
            cmd = ["flameshot", "full", "--path", str(out_path.parent),
                   "--filename", out_path.name]

        result = subprocess.run(cmd, timeout=60)
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

# ── mac ──────────────────────────────────────────────────────
def _mac_capture(mode: str, out_path: Path) -> bool:
    try:
        if mode == MODE_ANNOTATE:
            # interactive selection on mac
            cmd = ["screencapture", "-i", str(out_path)]
        else:
            cmd = ["screencapture", str(out_path)]

        result = subprocess.run(cmd, timeout=30)
        return result.returncode == 0

    except Exception:
        return False

# ── windows ──────────────────────────────────────────────────
def _windows_capture(out_path: Path) -> bool:
    return _pyautogui_capture(out_path)

# ── pyautogui fallback ───────────────────────────────────────
def _pyautogui_capture(out_path: Path) -> bool:
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(str(out_path))
        return True
    except Exception:
        return False

# ── get active window title ───────────────────────────────────
def get_window_title() -> str:
    try:
        if OS == "Linux":
            return _linux_window_title()
        elif OS == "Darwin":
            return _mac_window_title()
        elif OS == "Windows":
            return _windows_window_title()
    except Exception:
        pass
    return "unknown"

def _linux_window_title() -> str:
    result = subprocess.run(
        ["xdotool", "getactivewindow", "getwindowname"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "unknown"

def _mac_window_title() -> str:
    script = (
        'tell application "System Events" to '
        'get name of first application process '
        'whose frontmost is true'
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "unknown"

def _windows_window_title() -> str:
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or "unknown"
    except Exception:
        return "unknown"