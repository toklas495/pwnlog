import threading
import customtkinter as ctk
from typing import Optional

from ui.theme import apply_window_style
from ui.dashboard import Dashboard
from ui.popup import QuickLogPopup
from core.hotkey import HotkeyListener
from core.project import init_pwnlog


# ── app controller ───────────────────────────────────────────
class PwnLog:

    def __init__(self) -> None:
        self.dashboard : Optional[Dashboard]      = None
        self.popup     : Optional[QuickLogPopup]  = None
        self.hotkey    : Optional[HotkeyListener] = None

    # ── boot sequence ─────────────────────────────────────────
    def start(self) -> None:
        init_pwnlog()
        self._start_dashboard()
        self._start_hotkey()
        self.dashboard.mainloop()

    # ── dashboard ─────────────────────────────────────────────
    def _start_dashboard(self) -> None:
        self.dashboard = Dashboard()
        self.dashboard.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

    # ── global hotkey ─────────────────────────────────────────
    def _start_hotkey(self) -> None:
        self.hotkey = HotkeyListener(
            on_trigger=self._open_popup,
        )
        self.hotkey.start()

    # ── open popup — always called from hotkey thread ─────────
    def _open_popup(self) -> None:
        # must schedule on main thread
        if self.dashboard:
            self.dashboard.after(0, self._show_popup)

    # ── show popup on main thread ─────────────────────────────
    def _show_popup(self) -> None:
        # only one popup at a time
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return

        self.popup = QuickLogPopup(
            master   = self.dashboard,
            on_saved = self.dashboard.on_entry_saved,
        )

    # ── clean shutdown ────────────────────────────────────────
    def _on_close(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        if self.dashboard:
            self.dashboard.destroy()


# ── entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        app = PwnLog()
        app.start()
    except KeyboardInterrupt:
        pass