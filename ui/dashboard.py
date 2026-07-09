import customtkinter as ctk
from tkinter import StringVar
from typing import Optional

from ui.theme import (
    THEME, CATEGORIES, FONT_TITLE, FONT_BODY,
    FONT_SMALL, FONT_MONO, button_style,
    card_style, label_style, apply_window_style,
    apply_window_icon, get_logo_image,
)
from core.project import (
    list_projects, create_project,
    set_active_project, get_active_project_name,
    delete_project, list_templates, DEFAULT_TEMPLATE,
)
from core.logger import (
    get_entries, filter_entries,
    get_todays_entries, category_counts,
)


# ── main dashboard window ────────────────────────────────────
class Dashboard(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()
        self.active_filter = StringVar(value="All")
        self._filter_buttons = {}
        self._setup_window()
        self._build_ui()
        self._refresh()

    # ── window setup ─────────────────────────────────────────
    def _setup_window(self) -> None:
        self.title("PwnLog")
        self.geometry("900x620")
        self.minsize(800, 500)
        apply_window_style(self)
        apply_window_icon(self)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    # ── build full ui ─────────────────────────────────────────
    def _build_ui(self) -> None:
        self._build_sidebar()
        self._build_main_panel()

    # ─────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────
    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=THEME["bg_secondary"],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self._build_logo()
        self._build_project_section()
        self._build_filter_section()
        self._build_stats_section()

    # ── logo ─────────────────────────────────────────────────
    def _build_logo(self) -> None:
        frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=THEME["bg_primary"],
            corner_radius=0,
            height=52,
        )
        frame.pack(fill="x")
        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame,
            image=get_logo_image(22),
            text="",
        ).pack(side="left", padx=(16, 8), pady=14)

        ctk.CTkLabel(
            frame,
            text="PwnLog",
            font=FONT_TITLE(),
            text_color=THEME["text_primary"],
        ).pack(side="left", pady=14)

    # ── project section ───────────────────────────────────────
    def _build_project_section(self) -> None:
        ctk.CTkLabel(
            self.sidebar,
            text="Project",
            font=FONT_SMALL(),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", padx=14, pady=(18, 6))

        # project dropdown
        self.project_var = StringVar(
            value=get_active_project_name() or "No project"
        )
        self.project_menu = ctk.CTkOptionMenu(
            self.sidebar,
            variable=self.project_var,
            values=self._get_project_list(),
            fg_color=THEME["bg_card"],
            button_color=THEME["bg_card"],
            button_hover_color=THEME["bg_secondary"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_hover_color=THEME["bg_secondary"],
            text_color=THEME["text_primary"],
            font=FONT_SMALL(),
            corner_radius=6,
            command=self._on_project_switch,
        )
        self.project_menu.pack(fill="x", padx=14)

        # new project input row
        input_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        input_frame.pack(fill="x", padx=14, pady=(8, 0))

        self.new_project_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="New project…",
            height=32,
            fg_color=THEME["bg_card"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_primary"],
            placeholder_text_color=THEME["text_secondary"],
            font=FONT_SMALL(),
            corner_radius=6,
        )
        self.new_project_input.pack(side="left", fill="x", expand=True)
        self.new_project_input.bind(
            "<Return>", lambda e: self._create_project()
        )

        ctk.CTkButton(
            input_frame,
            text="+",
            width=32,
            height=32,
            corner_radius=6,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_dim"],
            text_color=THEME["bg_primary"],
            font=FONT_BODY(),
            command=self._create_project,
        ).pack(side="right", padx=(6, 0))

        # template picker — collapses to "default" so typing a name + Enter
        # still works exactly like before; only touch this if you want a
        # different directory shape (see ~/.pwnlog/templates/*.json)
        self.template_var = StringVar(value=DEFAULT_TEMPLATE)
        template_names = list_templates()
        if len(template_names) > 1:
            ctk.CTkOptionMenu(
                self.sidebar,
                variable=self.template_var,
                values=template_names,
                width=140,
                height=24,
                corner_radius=6,
                fg_color=THEME["bg_card"],
                button_color=THEME["bg_card"],
                button_hover_color=THEME["border"],
                text_color=THEME["text_secondary"],
                dropdown_fg_color=THEME["bg_card"],
                font=FONT_SMALL(),
            ).pack(fill="x", padx=14, pady=(6, 0))

    # ── filter section ────────────────────────────────────────
    def _build_filter_section(self) -> None:
        self._filter_buttons = {}
        ctk.CTkLabel(
            self.sidebar,
            text="Filter",
            font=FONT_SMALL(),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", padx=14, pady=(22, 6))

        # all button
        self._build_filter_btn("All", THEME["accent"])

        for cat, color in CATEGORIES.items():
            self._build_filter_btn(cat, color)

    def _build_filter_btn(self, label: str, color: str) -> None:
        is_active = self.active_filter.get() == label

        btn = ctk.CTkButton(
            self.sidebar,
            text=label,
            height=28,
            anchor="w",
            corner_radius=6,
            fg_color=color if is_active else "transparent",
            hover_color=THEME["bg_card"],
            text_color=THEME["bg_primary"] if is_active else color,
            font=FONT_SMALL(),
            command=lambda l=label: self._apply_filter(l),
        )
        btn.pack(fill="x", padx=14, pady=2)
        self._filter_buttons[label] = (btn, color)

    # ── stats section ─────────────────────────────────────────
    def _build_stats_section(self) -> None:
        counts  = category_counts()
        today   = get_todays_entries()
        total   = get_entries()

        frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=THEME["bg_card"],
            corner_radius=8,
        )
        frame.pack(fill="x", padx=14, pady=(20, 0))

        rows = [
            ("Total entries", str(len(total))),
            ("Today",         str(len(today))),
        ]

        for label, value in rows:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(
                row,
                text=label,
                font=FONT_SMALL(),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(side="left")

            value_label = ctk.CTkLabel(
                row,
                text=value,
                font=FONT_SMALL(),
                text_color=THEME["accent"],
                anchor="e",
            )
            value_label.pack(side="right")

            if label == "Total entries":
                self.stats_total_label = value_label
            elif label == "Today":
                self.stats_today_label = value_label

    # ─────────────────────────────────────────────────────────
    # MAIN PANEL
    # ─────────────────────────────────────────────────────────
    def _build_main_panel(self) -> None:
        self.main = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_primary"],
            corner_radius=0,
        )
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_entries_panel()

    # ── top bar ───────────────────────────────────────────────
    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(
            self.main,
            fg_color=THEME["bg_secondary"],
            corner_radius=0,
            height=52,
        )
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)

        project = get_active_project_name() or "no project"

        self.project_label = ctk.CTkLabel(
            bar,
            text=project,
            font=FONT_BODY(),
            text_color=THEME["text_primary"],
        )
        self.project_label.pack(side="left", padx=16, pady=14)

        ctk.CTkLabel(
            bar,
            text="Alt+Shift+Z to log",
            font=FONT_SMALL(),
            text_color=THEME["text_secondary"],
        ).pack(side="right", padx=16)

    # ── entries panel ─────────────────────────────────────────
    def _build_entries_panel(self) -> None:
        self.entries_frame = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
        )
        self.entries_frame.grid(
            row=1, column=0,
            sticky="nsew",
            padx=0, pady=0,
        )
        self.entries_frame.grid_columnconfigure(0, weight=1)

    # ── render entries ────────────────────────────────────────
    def _render_entries(self) -> None:
        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        category = self.active_filter.get()
        entries  = filter_entries(category)

        if not entries:
            self._render_empty_state()
            return

        # newest first
        for entry in reversed(entries):
            self._render_entry_card(entry)

    # ── single entry card ─────────────────────────────────────
    def _render_entry_card(self, entry: dict) -> None:
        category = entry.get("category", "Note")
        color    = CATEGORIES.get(category, THEME["text_secondary"])
        time_str = entry["timestamp"][11:16]

        card = ctk.CTkFrame(
            self.entries_frame,
            fg_color=THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", padx=16, pady=5)
        card.grid_columnconfigure(1, weight=1)

        # color accent bar
        accent = ctk.CTkFrame(
            card,
            width=4,
            fg_color=color,
            corner_radius=0,
        )
        accent.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 12))

        # header row
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=1, sticky="ew", pady=(10, 2))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=category,
            font=FONT_SMALL(),
            text_color=color,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=time_str,
            font=FONT_SMALL(),
            text_color=THEME["text_secondary"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=(0, 12))

        # note text
        ctk.CTkLabel(
            card,
            text=entry.get("note", ""),
            font=FONT_BODY(),
            text_color=THEME["text_primary"],
            anchor="w",
            wraplength=560,
            justify="left",
        ).grid(row=1, column=1, sticky="ew", pady=(0, 4))

        # window title
        window = entry.get("window_title", "")
        if window and window != "unknown":
            ctk.CTkLabel(
                card,
                text=f"↳ {window}",
                font=FONT_SMALL(),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=2, column=1, sticky="w", pady=(0, 10))

        # screenshot badge
        if entry.get("screenshot"):
            ctk.CTkLabel(
                card,
                text="📎 screenshot attached",
                font=FONT_SMALL(),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=3, column=1, sticky="w", pady=(0, 10))

    # ── empty state ───────────────────────────────────────────
    def _render_empty_state(self) -> None:
        ctk.CTkLabel(
            self.entries_frame,
            text="No entries yet\nPress Alt+Shift+Z to start logging",
            font=FONT_BODY(),
            text_color=THEME["text_secondary"],
            justify="center",
        ).pack(expand=True, pady=80)

    # ─────────────────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────────────────
    def _create_project(self) -> None:
        name = self.new_project_input.get().strip()
        if not name:
            return
        template = getattr(self, "template_var", None)
        template = template.get() if template else DEFAULT_TEMPLATE
        try:
            create_project(name, template=template)
            self.new_project_input.delete(0, "end")
            self._refresh()
        except FileExistsError:
            pass

    def _on_project_switch(self, selected: str) -> None:
        set_active_project(selected)
        self._refresh()

    def _apply_filter(self, category: str) -> None:
        self.active_filter.set(category)
        self._refresh()

    def _get_project_list(self) -> list[str]:
        projects = list_projects()
        return projects if projects else ["No project"]

    # ── full refresh ──────────────────────────────────────────
    def _refresh(self) -> None:
        self._refresh_projects()
        self._refresh_filters()
        self._refresh_stats()
        self._render_entries()

    def _refresh_projects(self) -> None:
        projects = self._get_project_list()
        active = get_active_project_name() or "No project"

        if active not in projects and projects:
            active = projects[0]
            if active != "No project":
                set_active_project(active)

        self.project_menu.configure(values=projects)
        self.project_var.set(active)
        self.project_label.configure(text=active)

    def _refresh_filters(self) -> None:
        active = self.active_filter.get()
        for label, (btn, color) in self._filter_buttons.items():
            is_active = active == label
            btn.configure(
                fg_color=color if is_active else "transparent",
                text_color=THEME["bg_primary"] if is_active else color,
            )

    def _refresh_stats(self) -> None:
        today = get_todays_entries()
        total = get_entries()

        if hasattr(self, "stats_total_label"):
            self.stats_total_label.configure(text=str(len(total)))
        if hasattr(self, "stats_today_label"):
            self.stats_today_label.configure(text=str(len(today)))

    # ── called by hotkey after save ───────────────────────────
    def on_entry_saved(self) -> None:
        self.after(0, self._refresh)