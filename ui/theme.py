import customtkinter as ctk
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image

# ── appearance ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── theme constants ──────────────────────────────────────────
THEME: Dict[str, Any] = {
    "bg_primary"     : "#0f141a",
    "bg_secondary"   : "#131a22",
    "bg_card"        : "#18212b",
    "accent"         : "#1bb7a1",
    "accent_dim"     : "#129486",
    "text_primary"   : "#e6edf3",
    "text_secondary" : "#8b97a6",
    "danger"         : "#e76565",
    "warning"        : "#f2b45b",
    "border"         : "#223041",
    "font_main"      : "Cantarell",
    "font_size"      : 13,
}

# ── category colors ──────────────────────────────────────────
CATEGORIES: Dict[str, str] = {
    "Recon"    : "#23c6a6",
    "Auth"     : "#f0b96c",
    "IDOR"     : "#f29c6b",
    "XSS"      : "#e46f6f",
    "SQLi"     : "#c68be6",
    "SSRF"     : "#6da6ff",
    "LFI"      : "#e28fb1",
    "Logic"    : "#e3d36b",
    "Dead End" : "#5c6b7a",
    "Note"     : "#9aa6b2",
}

# ── fonts ────────────────────────────────────────────────────
def font(size: int = None, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(
        family=THEME["font_main"],
        size=size or THEME["font_size"],
        weight=weight,
    )

FONT_BODY  = lambda: font(13)
FONT_SMALL = lambda: font(11)
FONT_TITLE = lambda: font(15, "bold")
FONT_MONO  = lambda: font(12)

# ── reusable widget styles ───────────────────────────────────
def apply_window_style(window: ctk.CTk | ctk.CTkToplevel) -> None:
    window.configure(fg_color=THEME["bg_primary"])

def apply_window_icon(window: ctk.CTk | ctk.CTkToplevel) -> None:
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    icon_path = assets_dir / "favicon.ico"
    legacy_path = assets_dir / "icon.ico"
    target = icon_path if icon_path.exists() else legacy_path
    if not target.exists():
        return
    try:
        window.iconbitmap(str(target))
    except Exception:
        pass

_LOGO_CACHE: Dict[int, Optional[ctk.CTkImage]] = {}

def get_logo_image(size: int = 24) -> Optional[ctk.CTkImage]:
    if size in _LOGO_CACHE:
        return _LOGO_CACHE[size]

    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    logo_path = assets_dir / "android-chrome-192x192.png"
    if not logo_path.exists():
        _LOGO_CACHE[size] = None
        return None

    try:
        image = Image.open(logo_path)
        logo = ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
    except Exception:
        logo = None

    _LOGO_CACHE[size] = logo
    return logo

def card_style() -> Dict[str, Any]:
    return {
        "fg_color"    : THEME["bg_card"],
        "corner_radius": 8,
        "border_width": 1,
        "border_color": THEME["border"],
    }

def button_style(accent: bool = False) -> Dict[str, Any]:
    return {
        "fg_color"          : THEME["accent"] if accent else THEME["bg_card"],
        "hover_color"       : THEME["accent_dim"] if accent else THEME["bg_secondary"],
        "text_color"        : THEME["bg_primary"] if accent else THEME["text_primary"],
        "corner_radius"     : 6,
        "font"              : font(13, "bold") if accent else font(13),
        "border_width"      : 0 if accent else 1,
        "border_color"      : THEME["border"],
    }

def input_style() -> Dict[str, Any]:
    return {
        "fg_color"          : THEME["bg_secondary"],
        "border_color"      : THEME["border"],
        "border_width"      : 1,
        "text_color"        : THEME["text_primary"],
        "placeholder_text_color": THEME["text_secondary"],
        "corner_radius"     : 6,
        "font"              : font(13),
    }

def label_style(secondary: bool = False) -> Dict[str, Any]:
    return {
        "text_color" : THEME["text_secondary"] if secondary else THEME["text_primary"],
        "font"       : font(11) if secondary else font(13),
    }