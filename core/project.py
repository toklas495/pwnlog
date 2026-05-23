import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECTS_DIR = Path.home() / ".pwnlog" / "projects"
CONFIG_FILE  = Path.home() / ".pwnlog" / "config.json"

# ── folder structure for every project ──────────────────────
FOLDERS = [
    "screenshots",
    "exports",
]

# ── ensure base dirs exist on startup ────────────────────────
def init_pwnlog() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        _write_config({"active_project": None})

    config = _read_config()
    active = config.get("active_project")
    if active and not (PROJECTS_DIR / active).exists():
        config["active_project"] = None
        _write_config(config)

    projects = list_projects()
    if not projects:
        create_project("inbox")
    elif not config.get("active_project"):
        set_active_project(projects[0])

# ── create a new project ─────────────────────────────────────
def create_project(name: str) -> Path:
    slug = _slugify(name)
    project_path = PROJECTS_DIR / slug

    if project_path.exists():
        raise FileExistsError(f"Project '{slug}' already exists.")

    project_path.mkdir(parents=True)

    for folder in FOLDERS:
        (project_path / folder).mkdir()

    _init_journal(project_path, name)
    _init_timeline(project_path, name)
    set_active_project(slug)

    return project_path

# ── switch active project ────────────────────────────────────
def set_active_project(slug: str) -> None:
    config = _read_config()
    config["active_project"] = slug
    _write_config(config)

# ── get active project path ──────────────────────────────────
def get_active_project() -> Optional[Path]:
    config = _read_config()
    slug   = config.get("active_project")

    if not slug:
        return None

    path = PROJECTS_DIR / slug
    return path if path.exists() else None

# ── get active project name ──────────────────────────────────
def get_active_project_name() -> Optional[str]:
    config = _read_config()
    return config.get("active_project")

# ── list all projects ────────────────────────────────────────
def list_projects() -> list[str]:
    if not PROJECTS_DIR.exists():
        return []
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]

# ── delete a project ─────────────────────────────────────────
def delete_project(slug: str) -> None:
    project_path = PROJECTS_DIR / slug

    if not project_path.exists():
        raise FileNotFoundError(f"Project '{slug}' not found.")

    shutil.rmtree(project_path)

    config = _read_config()
    if config.get("active_project") == slug:
        config["active_project"] = None
        _write_config(config)

# ── init journal.md ──────────────────────────────────────────
def _init_journal(project_path: Path, name: str) -> None:
    journal = project_path / "journal.md"
    journal.write_text(
        f"# {name}\n"
        f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"---\n\n",
        encoding="utf-8",
    )

# ── init timeline.json ───────────────────────────────────────
def _init_timeline(project_path: Path, name: str) -> None:
    timeline = project_path / "timeline.json"
    timeline.write_text(
        json.dumps({
            "project" : name,
            "created" : datetime.now().isoformat(),
            "entries" : [],
        }, indent=2),
        encoding="utf-8",
    )

# ── config helpers ───────────────────────────────────────────
def _read_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

def _write_config(data: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ── slug helper ──────────────────────────────────────────────
def _slugify(name: str) -> str:
    return (
        name.lower()
            .strip()
            .replace(" ", "-")
            .replace("/", "-")
            .replace("\\", "-")
            .replace(".", "-")
    )