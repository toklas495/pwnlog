import customtkinter as ctk
from tkinter import StringVar
from typing import Optional, Callable

from ui.theme import THEME, CATEGORIES, FONT_TITLE, FONT_BODY, FONT_SMALL, apply_window_icon, get_logo_image
from core.logger import save_entry
from core.screenshot import capture, get_window_title, MODE_ANNOTATE


class QuickLogPopup(ctk.CTkToplevel):

    def __init__(self, master=None, on_saved=None) -> None:
        super().__init__(master)

        self.on_saved     = on_saved
        self.window_title = get_window_title()
        self.screenshot_mode = StringVar(value=MODE_ANNOTATE)
        self.active_category = StringVar(value="Note")
        self._cat_buttons    = {}

        # ── window ───────────────────────────────────────────
        self.title("")
        self.geometry("380x440")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        apply_window_icon(self)
        self.attributes("-topmost", True)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 190
        y = (self.winfo_screenheight() // 2) - 220
        self.geometry(f"+{x}+{y}")

        # ── header ───────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], corner_radius=0, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, image=get_logo_image(20), text="").pack(side="left", padx=(16, 8))
        ctk.CTkLabel(header, text="PwnLog", font=FONT_TITLE(), text_color=THEME["text_primary"]).pack(side="left")
        ctk.CTkLabel(header, text="Alt+Shift+Z", font=FONT_SMALL(), text_color=THEME["text_secondary"]).pack(side="right", padx=16)

        # ── note label ───────────────────────────────────────
        ctk.CTkLabel(self, text="Note", font=FONT_SMALL(), text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=(14, 4))

        # ── note input ───────────────────────────────────────
        self.note_input = ctk.CTkTextbox(
            self,
            height=100,
            wrap="word",
            fg_color=THEME["bg_secondary"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            font=FONT_SMALL(),
        )
        self.note_input.pack(fill="x", padx=16)

        # ── category label ───────────────────────────────────
        ctk.CTkLabel(self, text="Category", font=FONT_SMALL(), text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=(12, 6))

        # ── category pills ───────────────────────────────────
        cat_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=40, orientation="horizontal")
        cat_frame.pack(fill="x", padx=16)

        for cat, color in CATEGORIES.items():
            btn = ctk.CTkButton(
                cat_frame,
                text=cat,
                width=70,
                height=28,
                corner_radius=20,
                fg_color="transparent",
                border_width=1,
                border_color=color,
                text_color=color,
                hover_color=THEME["bg_card"],
                font=FONT_SMALL(),
                command=lambda c=cat: self._select(c),
            )
            btn.pack(side="left", padx=3)
            self._cat_buttons[cat] = btn

        self._select("Note")

        # ── active window context ────────────────────────────
        short = self.window_title[:45] + "…" if len(self.window_title) > 45 else self.window_title
        ctk.CTkLabel(self, text=f"↳ {short}", font=FONT_SMALL(), text_color=THEME["text_secondary"], anchor="w").pack(fill="x", padx=16, pady=(10, 0))

        # ── save button ──────────────────────────────────────
        ctk.CTkButton(
            self,
            text="Save  ↵",
            height=40,
            command=self._save,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_dim"],
            text_color=THEME["bg_primary"],
            corner_radius=6,
            font=FONT_BODY(),
        ).pack(fill="x", padx=16, pady=14)

        # ── bindings ─────────────────────────────────────────
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Tab>",    lambda e: self._cycle())
        self.after(100, self.note_input.focus_set)

        self.note_input.bind("<Return>", self._on_enter)
        self.note_input.bind("<Shift-Return>", self._on_shift_enter)
        self.note_input.bind("<Tab>", self._on_tab)

    def _on_enter(self, event=None):
        self._save()
        return "break"

    def _on_shift_enter(self, event=None):
        self.note_input.insert("insert", "\n")
        return "break"

    def _on_tab(self, event=None):
        self._cycle()
        return "break"

    # ── select category ──────────────────────────────────────
    def _select(self, cat: str) -> None:
        self.active_category.set(cat)
        for name, btn in self._cat_buttons.items():
            color = CATEGORIES[name]
            if name == cat:
                btn.configure(fg_color=color, text_color=THEME["bg_primary"])
            else:
                btn.configure(fg_color="transparent", text_color=color)

    # ── cycle categories with Tab ────────────────────────────
    def _cycle(self) -> None:
        cats    = list(CATEGORIES.keys())
        current = self.active_category.get()
        idx     = cats.index(current) if current in cats else 0
        self._select(cats[(idx + 1) % len(cats)])

    # ── save ─────────────────────────────────────────────────
    def _save(self) -> None:
        note = self.note_input.get("1.0", "end").strip()

        if not note:
            x, y = self.winfo_x(), self.winfo_y()
            for i, o in enumerate([10, -10, 6, -6, 2, -2, 0]):
                self.after(i * 30, lambda v=o: self.geometry(f"+{x+v}+{y}"))
            return

        category = self.active_category.get()
        mode     = self.screenshot_mode.get()
        title    = self.window_title

        self.destroy()

        def after_screenshot(path):
            save_entry(note=note, category=category, screenshot=path, window_title=title)
            if self.on_saved:
                self.on_saved()

        capture(note=note, category=category, mode=mode, on_done=after_screenshot)