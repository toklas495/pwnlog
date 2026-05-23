import threading
from typing import Callable, Optional
from pynput import keyboard

# ── hotkey combination ───────────────────────────────────────
TRIGGER = {
    keyboard.Key.alt_l,
    keyboard.KeyCode.from_char('z'),
    keyboard.Key.shift,
}

# ── listener class ───────────────────────────────────────────
class HotkeyListener:

    def __init__(self, on_trigger: Callable[[], None]) -> None:
        self.on_trigger   : Callable[[], None] = on_trigger
        self.pressed_keys : set             = set()
        self._listener    : Optional[object] = None
        self._lock        : threading.Lock  = threading.Lock()

    # ── start listening ──────────────────────────────────────
    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press   = self._on_press,
            on_release = self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    # ── stop listening ───────────────────────────────────────
    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    # ── key press handler ────────────────────────────────────
    def _on_press(self, key) -> None:
        with self._lock:
            self.pressed_keys.add(self._normalize(key))
            if self._is_triggered():
                self.pressed_keys.clear()
                # fire in separate thread — never block listener
                threading.Thread(
                    target=self.on_trigger,
                    daemon=True,
                ).start()

    # ── key release handler ──────────────────────────────────
    def _on_release(self, key) -> None:
        with self._lock:
            self.pressed_keys.discard(self._normalize(key))

    # ── check if trigger combo is pressed ────────────────────
    def _is_triggered(self) -> bool:
        return all(k in self.pressed_keys for k in TRIGGER)

    # ── normalize key for consistent comparison ───────────────
    def _normalize(self, key) -> any:
        try:
            # normalize both alt keys to alt_l
            if key in (keyboard.Key.alt_r, keyboard.Key.alt_l):
                return keyboard.Key.alt_l
            # normalize both shift keys to shift
            if key in (keyboard.Key.shift, keyboard.Key.shift_r):
                return keyboard.Key.shift
            # normalize letter keys to lowercase (shifted Z -> z)
            if isinstance(key, keyboard.KeyCode) and key.char:
                return keyboard.KeyCode.from_char(key.char.lower())
            return key
        except Exception:
            return key