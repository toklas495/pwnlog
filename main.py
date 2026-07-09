import argparse
import threading
import customtkinter as ctk
from typing import Optional

from ui.popup import QuickLogPopup
from core.hotkey import HotkeyListener
from core.project import init_pwnlog, get_active_project_name


# ── background listener — the default way to run pwnlog ───────
# no dashboard window, no visible UI at all until you hit the
# hotkey. manage projects with cli.py instead.
class PwnLogListener:

    def __init__(self) -> None:
        self.root   : Optional[ctk.CTk]          = None
        self.popup  : Optional[QuickLogPopup]    = None
        self.hotkey : Optional[HotkeyListener]   = None

    def start(self) -> None:
        init_pwnlog()
        self._start_hidden_root()
        self._start_hotkey()

        project = get_active_project_name() or "no project"
        print(f"[pwnlog] listening — Alt+Shift+Z to log  (project: {project})")
        print("[pwnlog] ctrl+c to stop. use `python cli.py` to manage projects.")

        self.root.mainloop()

    def _start_hidden_root(self) -> None:
        self.root = ctk.CTk()
        self.root.withdraw()  # no visible window

    def _start_hotkey(self) -> None:
        self.hotkey = HotkeyListener(on_trigger=self._open_popup)
        self.hotkey.start()

    def _open_popup(self) -> None:
        # must schedule on main thread
        self.root.after(0, self._show_popup)

    def _show_popup(self) -> None:
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return
        self.popup = QuickLogPopup(master=self.root)

    def stop(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        if self.root:
            self.root.destroy()


# ── optional visual dashboard — python main.py --dashboard ────
class PwnLogDashboard:

    def __init__(self) -> None:
        self.dashboard = None
        self.popup     = None
        self.hotkey    = None

    def start(self) -> None:
        from ui.dashboard import Dashboard

        init_pwnlog()
        self.dashboard = Dashboard()
        self.dashboard.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_hotkey()
        self.dashboard.mainloop()

    def _start_hotkey(self) -> None:
        self.hotkey = HotkeyListener(on_trigger=self._open_popup)
        self.hotkey.start()

    def _open_popup(self) -> None:
        self.dashboard.after(0, self._show_popup)

    def _show_popup(self) -> None:
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return
        self.popup = QuickLogPopup(master=self.dashboard, on_saved=self.dashboard.on_entry_saved)

    def _on_close(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        if self.dashboard:
            self.dashboard.destroy()


# ── entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PwnLog")
    parser.add_argument(
        "--dashboard", action="store_true",
        help="open the visual dashboard instead of running as a background listener",
    )
    args = parser.parse_args()

    app = PwnLogDashboard() if args.dashboard else PwnLogListener()

    try:
        app.start()
    except KeyboardInterrupt:
        if hasattr(app, "stop"):
            app.stop()
