import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.project import (
    PROJECTS_DIR, get_active_project, get_host_dir, ensure_recon_tree,
)

# how long after an import a new journal entry will auto-link to it
LAST_IMPORT_WINDOW_MIN = 15

STATE_FILENAME = ".pwnlog_state.json"

# ── where a --type import lands, if no --host is given ───────
TYPE_FOLDERS = {
    "subdomains" : "01-recon/passive/subdomains",
    "dorks"      : "01-recon/passive/google_dorks",
    "github"     : "01-recon/passive/github_dorks",
    "asn"        : "01-recon/passive",
    "whois"      : "01-recon/passive",
    "resolved"   : "01-recon/active",
    "httpx"      : "01-recon/active",
    "endpoints"  : "03-discovery/endpoints",
    "js"         : "03-discovery/js_files",
    "directories": "03-discovery/directories",
    "params"     : "03-discovery/params",
    "apis"       : "03-discovery/apis",
}

DEFAULT_FOLDER = "01-recon/passive"


# ── main import function ──────────────────────────────────────
def import_file(
    src          : Path,
    project_path : Optional[Path] = None,
    host         : Optional[str] = None,
    ftype        : Optional[str] = None,
) -> Path:
    src = Path(src)
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"File not found: {src}")

    project_path = project_path or get_active_project()
    if not project_path:
        raise RuntimeError("No active project. Set one first.")

    ensure_recon_tree(project_path)

    if host:
        dest_dir = get_host_dir(project_path, host)
    else:
        rel = TYPE_FOLDERS.get(ftype, DEFAULT_FOLDER)
        dest_dir = project_path / rel
        dest_dir.mkdir(parents=True, exist_ok=True)

    dest = _unique_path(dest_dir / src.name)
    shutil.copy2(src, dest)

    _record_last_import(project_path, dest, host)

    return dest


# ── avoid clobbering an existing file with the same name ─────
def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    i = 2
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


# ── state tracking, for auto-linking in the journal ───────────
def _state_path(project_path: Path) -> Path:
    return project_path / STATE_FILENAME

def _read_state(project_path: Path) -> dict:
    path = _state_path(project_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_state(project_path: Path, state: dict) -> None:
    _state_path(project_path).write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )

def _record_last_import(project_path: Path, dest: Path, host: Optional[str]) -> None:
    state = _read_state(project_path)
    state["last_import"] = {
        "path"      : str(dest.relative_to(project_path)),
        "host"      : host,
        "timestamp" : datetime.now().isoformat(),
        "consumed"  : False,
    }
    _write_state(project_path, state)

# ── used by logger.py right before writing a new entry ────────
def get_recent_import(project_path: Path) -> Optional[dict]:
    state = _read_state(project_path)
    last  = state.get("last_import")

    if not last or last.get("consumed"):
        return None

    age_min = (
        datetime.now() - datetime.fromisoformat(last["timestamp"])
    ).total_seconds() / 60

    if age_min > LAST_IMPORT_WINDOW_MIN:
        return None

    return last

def mark_import_consumed(project_path: Path) -> None:
    state = _read_state(project_path)
    if "last_import" in state:
        state["last_import"]["consumed"] = True
        _write_state(project_path, state)
