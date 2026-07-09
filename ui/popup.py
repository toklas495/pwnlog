import customtkinter as ctk
from tkinter import StringVar
from typing import Optional, Callable

from ui.theme import THEME, CATEGORIES, FONT_TITLE, FONT_BODY, FONT_SMALL, apply_window_icon, get_logo_image
from core.logger import save_entry, get_todays_entries
from core.screenshot import capture, get_window_title, MODE_ANNOTATE, MODE_NONE
from core.project import get_active_project
from core.tags import get_recent_tags, record_tag

# ── number-key shortcuts, in category order: 1 2 3 4 5 6 7 8 9 0 ─
_DIGIT_KEYS      = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
_SUPERSCRIPT_MAP = {"1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
                     "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "0": "⁰"}


class QuickLogPopup(ctk.CTkToplevel):

    def __init__(self, master=None, on_saved=None) -> None:
        super().__init__(master)

        self.on_saved         = on_saved
        self.window_title     = get_window_title()
        self.screenshot_mode  = StringVar(value=MODE_ANNOTATE)
        self.active_category  = StringVar(value="Note")
        self._cat_buttons     = {}
        self._digit_to_cat    = dict(zip(_DIGIT_KEYS, CATEGORIES.keys()))

        # ── window ───────────────────────────────────────────
        self.title("")
        self.geometry("420x536")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg_primary"])
        apply_window_icon(self)
        self.attributes("-topmost", True)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 210
        y = (self.winfo_screenheight() // 2) - 268
        self.geometry(f"+{x}+{y}")

        # ── signature accent stripe ────────────────────────────
        ctk.CTkFrame(self, fg_color=THEME["accent"], corner_radius=0, height=3).pack(fill="x")

        # ── header ───────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=THEME["bg_secondary"], corner_radius=0, height=46)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, image=get_logo_image(18), text="").pack(side="left", padx=(16, 6))
        ctk.CTkLabel(header, text="PwnLog", font=FONT_TITLE(), text_color=THEME["text_primary"]).pack(side="left")

        # screenshot on/off toggle — top right
        self.shot_btn = ctk.CTkButton(
            header, text="📸", width=32, height=28, corner_radius=6,
            fg_color=THEME["bg_card"], hover_color=THEME["border"],
            text_color=THEME["accent"], font=FONT_BODY(),
            command=self._toggle_screenshot,
        )
        self.shot_btn.pack(side="right", padx=(4, 14))

        # "logged today" counter — small momentum nudge
        today_count = len(get_todays_entries())
        self.streak_label = ctk.CTkLabel(
            header, text=f"{today_count} today", font=FONT_SMALL(),
            text_color=THEME["text_secondary"],
        )
        self.streak_label.pack(side="right", padx=(0, 4))

        # ── note input — the hero element, no label needed ────
        self.note_input = ctk.CTkTextbox(
            self,
            height=118,
            wrap="word",
            fg_color=THEME["bg_secondary"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_secondary"],
            corner_radius=8,
            font=FONT_BODY(),
        )
        self.note_input.pack(fill="x", padx=16, pady=(16, 14))

        self._placeholder      = "what did you find?"
        self._placeholder_live = True
        self.note_input.insert("1.0", self._placeholder)
        self.note_input.bind("<FocusIn>",  self._clear_placeholder)
        self.note_input.bind("<FocusOut>", self._restore_placeholder)

        # ── category grid — fixed 5x2, no scrolling ───────────
        cat_frame = ctk.CTkFrame(self, fg_color="transparent")
        cat_frame.pack(fill="x", padx=16)
        for col in range(5):
            cat_frame.grid_columnconfigure(col, weight=1)

        for i, (cat, color) in enumerate(CATEGORIES.items()):
            digit = _DIGIT_KEYS[i]
            row, col = divmod(i, 5)
            btn = ctk.CTkButton(
                cat_frame,
                text=f"{cat}",
                height=30,
                corner_radius=8,
                fg_color="transparent",
                border_width=1,
                border_color=color,
                text_color=color,
                hover_color=THEME["bg_card"],
                font=FONT_SMALL(),
                command=lambda c=cat: self._select(c),
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self._cat_buttons[cat] = btn

        self._select("Note")

        # ── custom tag — no fixed taxonomy, type anything ──────
        # (JWT, CORS, race condition, prototype pollution... whatever
        # this target actually needs — the 10 above are just defaults)
        self.project_path = get_active_project()

        tag_row = ctk.CTkFrame(self, fg_color="transparent")
        tag_row.pack(fill="x", padx=16, pady=(10, 0))

        self.custom_tag_entry = ctk.CTkEntry(
            tag_row,
            placeholder_text="or type your own tag…",
            height=30,
            fg_color=THEME["bg_secondary"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_primary"],
            placeholder_text_color=THEME["text_secondary"],
            corner_radius=6,
            font=FONT_SMALL(),
        )
        self.custom_tag_entry.pack(fill="x")
        self.custom_tag_entry.bind("<Return>", self._on_enter)

        recent = get_recent_tags(self.project_path) if self.project_path else []
        if recent:
            chip_row = ctk.CTkFrame(self, fg_color="transparent")
            chip_row.pack(fill="x", padx=16, pady=(6, 0))
            ctk.CTkLabel(
                chip_row, text="recent:", font=FONT_SMALL(),
                text_color=THEME["border"],
            ).pack(side="left", padx=(0, 6))
            for tag in recent[:5]:
                ctk.CTkButton(
                    chip_row, text=tag, height=22, corner_radius=11,
                    fg_color=THEME["bg_card"], hover_color=THEME["border"],
                    text_color=THEME["text_secondary"], font=FONT_SMALL(),
                    command=lambda t=tag: self._fill_custom(t),
                ).pack(side="left", padx=2)

        # ── footer: window context + shortcut hint ────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(12, 6))

        short = self.window_title[:38] + "…" if len(self.window_title) > 38 else self.window_title
        ctk.CTkLabel(
            footer, text=f"↳ {short}", font=FONT_SMALL(),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            footer, text="⏎ save · esc close · ctrl+1‑0 tag", font=FONT_SMALL(),
            text_color=THEME["border"], anchor="e",
        ).pack(side="right")

        # ── save button ──────────────────────────────────────
        ctk.CTkButton(
            self,
            text="Save  ↵",
            height=42,
            command=self._save,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_dim"],
            text_color=THEME["bg_primary"],
            corner_radius=8,
            font=FONT_BODY(),
        ).pack(fill="x", padx=16, pady=(2, 16))

        # ── bindings ─────────────────────────────────────────
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Tab>",    lambda e: self._cycle())
        for digit, cat in self._digit_to_cat.items():
            self.bind(f"<Control-Key-{digit}>", lambda e, c=cat: self._select(c))
        self.after(100, self._focus_note)

        self.note_input.bind("<Return>", self._on_enter)
        self.note_input.bind("<Shift-Return>", self._on_shift_enter)
        self.note_input.bind("<Tab>", self._on_tab)

    # ── focus note input and clear placeholder immediately ────
    def _focus_note(self) -> None:
        self.note_input.focus_set()
        self._clear_placeholder()

    def _clear_placeholder(self, event=None) -> None:
        if self._placeholder_live:
            self.note_input.delete("1.0", "end")
            self.note_input.configure(text_color=THEME["text_primary"])
            self._placeholder_live = False

    def _restore_placeholder(self, event=None) -> None:
        if not self.note_input.get("1.0", "end").strip():
            self.note_input.insert("1.0", self._placeholder)
            self.note_input.configure(text_color=THEME["text_secondary"])
            self._placeholder_live = True

    def _on_enter(self, event=None):
        self._save()
        return "break"

    def _on_shift_enter(self, event=None):
        self.note_input.insert("insert", "\n")
        return "break"

    def _on_tab(self, event=None):
        self._cycle()
        return "break"

    # ── fill custom tag box from a recent chip ────────────────
    def _fill_custom(self, tag: str) -> None:
        self.custom_tag_entry.delete(0, "end")
        self.custom_tag_entry.insert(0, tag)
        self.custom_tag_entry.focus_set()

    # ── toggle screenshot on/off ──────────────────────────────
    def _toggle_screenshot(self) -> None:
        if self.screenshot_mode.get() == MODE_ANNOTATE:
            self.screenshot_mode.set(MODE_NONE)
            self.shot_btn.configure(text="🚫", text_color=THEME["text_secondary"])
        else:
            self.screenshot_mode.set(MODE_ANNOTATE)
            self.shot_btn.configure(text="📸", text_color=THEME["accent"])

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
        note = "" if self._placeholder_live else self.note_input.get("1.0", "end").strip()

        if not note:
            x, y = self.winfo_x(), self.winfo_y()
            for i, o in enumerate([10, -10, 6, -6, 2, -2, 0]):
                self.after(i * 30, lambda v=o: self.geometry(f"+{x+v}+{y}"))
            return

        custom_tag = self.custom_tag_entry.get().strip()
        category   = custom_tag if custom_tag else self.active_category.get()
        mode       = self.screenshot_mode.get()
        title      = self.window_title
        project    = self.project_path

        self.destroy()

        def after_screenshot(path):
            save_entry(note=note, category=category, screenshot=path, window_title=title)
            if custom_tag and project:
                record_tag(project, custom_tag)
            if self.on_saved:
                self.on_saved()

        capture(note=note, category=category, mode=mode, on_done=after_screenshot)
