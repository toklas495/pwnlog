import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.project import get_active_project
from core.importer import get_recent_import, mark_import_consumed
from ui.theme import CATEGORIES

# ── entry structure ──────────────────────────────────────────
def build_entry(
    note          : str,
    category      : str,
    screenshot    : Optional[str] = None,
    window_title  : Optional[str] = None,
    linked_file   : Optional[str] = None,
) -> dict:
    return {
        "id"           : _generate_id(),
        "timestamp"    : datetime.now().isoformat(),
        "category"     : category,
        "note"         : note.strip(),
        "window_title" : window_title or "unknown",
        "screenshot"   : screenshot or None,
        "linked_file"  : linked_file or None,
    }

# ── save entry — main function ───────────────────────────────
def save_entry(
    note          : str,
    category      : str,
    screenshot    : Optional[str] = None,
    window_title  : Optional[str] = None,
) -> bool:
    project_path = get_active_project()

    if not project_path:
        return False

    # if a file was imported (nmap, subfinder, etc.) in the last
    # few minutes, auto-link it under this entry — one time only
    linked_file = None
    recent = get_recent_import(project_path)
    if recent:
        linked_file = recent["path"]
        mark_import_consumed(project_path)

    entry = build_entry(note, category, screenshot, window_title, linked_file)

    _append_to_journal(project_path, entry)
    _append_to_timeline(project_path, entry)

    return True

# ── append to journal.md ─────────────────────────────────────
def _append_to_journal(project_path: Path, entry: dict) -> None:
    journal  = project_path / "journal.md"
    time_str = _format_time(entry["timestamp"])
    category = entry["category"]
    note     = entry["note"]
    window   = entry["window_title"]
    shot     = entry["screenshot"]
    linked   = entry.get("linked_file")

    block = f"## {time_str} — {category}\n\n"

    if window and window != "unknown":
        block += f"> {window}\n\n"

    block += f"{note}\n\n"

    if shot:
        filename = Path(shot).name
        block += f"![screenshot](screenshots/{filename})\n\n"

    if linked:
        filename = Path(linked).name
        block += f"📄 [{filename}]({linked})\n\n"

    block += "---\n\n"

    with journal.open("a", encoding="utf-8") as f:
        f.write(block)

# ── append to timeline.json ──────────────────────────────────
def _append_to_timeline(project_path: Path, entry: dict) -> None:
    timeline_path = project_path / "timeline.json"
    timeline      = json.loads(timeline_path.read_text(encoding="utf-8"))

    timeline["entries"].append(entry)

    timeline_path.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ── read all entries for a project ───────────────────────────
def get_entries(project_path: Optional[Path] = None) -> list[dict]:
    path = project_path or get_active_project()

    if not path:
        return []

    timeline_path = path / "timeline.json"

    if not timeline_path.exists():
        return []

    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    return data.get("entries", [])

# ── filter entries by category ───────────────────────────────
def filter_entries(category: str) -> list[dict]:
    entries = get_entries()
    if category == "All":
        return entries
    return [e for e in entries if e["category"] == category]

# ── get today's entries only ─────────────────────────────────
def get_todays_entries() -> list[dict]:
    today   = datetime.now().date().isoformat()
    entries = get_entries()
    return [
        e for e in entries
        if e["timestamp"].startswith(today)
    ]

# ── count entries per category ───────────────────────────────
def category_counts() -> dict[str, int]:
    entries = get_entries()
    counts  = {cat: 0 for cat in CATEGORIES}

    for entry in entries:
        cat = entry.get("category", "Note")
        counts[cat] = counts.get(cat, 0) + 1

    return counts

# ── helpers ──────────────────────────────────────────────────
def _generate_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def _format_time(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%Y-%m-%d %H:%M")

# ── generate smart filename from note text ───────────────────
def slugify_note(note: str, category: str) -> str:
    time_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    words    = (
        note.lower()
            .replace("/", " ")
            .replace(".", " ")
            .replace("-", " ")
            .split()
    )
    slug     = "_".join(words[:4])
    cat      = category.lower().replace(" ", "_")
    return f"{time_str}_{cat}_{slug}"