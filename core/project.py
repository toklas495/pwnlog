import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECTS_DIR      = Path.home() / ".pwnlog" / "projects"
CONFIG_FILE       = Path.home() / ".pwnlog" / "config.json"
TEMPLATES_DIR     = Path.home() / ".pwnlog" / "templates"                  # user-editable, lives outside the app
BUNDLED_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"   # shipped seed templates
DEFAULT_TEMPLATE  = "default"

# ── folder structure for every project, regardless of template ──
FOLDERS = [
    "screenshots",
    "exports",
]

# ── fallback tree, used only if templates/default.json can't be found ──
_FALLBACK_TEMPLATE = {
    "name": "default",
    "folders": [
        "01-recon/passive/subdomains", "01-recon/passive/google_dorks",
        "01-recon/passive/github_dorks", "01-recon/active",
        "02-hosts",
        "03-discovery/endpoints", "03-discovery/js_files",
        "03-discovery/directories", "03-discovery/params", "03-discovery/apis",
        "04-vuln-hunting/auth", "04-vuln-hunting/idor", "04-vuln-hunting/xss",
        "04-vuln-hunting/sqli", "04-vuln-hunting/ssrf", "04-vuln-hunting/lfi",
        "04-vuln-hunting/business-logic", "04-vuln-hunting/misc",
        "05-findings", "06-deadends", "07-report",
    ],
    "host_dir": "02-hosts",
    "findings_dir": "05-findings",
    "finding_template": (
        "# 000 — Finding Title\n\n**Category:**\n**Severity:**\n**Asset:**\n"
        "**Status:** Draft / Confirmed / Reported\n\n## Summary\n\n\n"
        "## Steps to reproduce\n1.\n\n## Evidence\n\n\n## Impact\n\n\n"
        "## Linked raw entries\n(timeline.json entry IDs)\n"
    ),
}

# ── ensure base dirs exist on startup ────────────────────────
def init_pwnlog() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _seed_templates()

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

    # backfill recon tree into any project created before this feature existed
    for slug in list_projects():
        ensure_recon_tree(PROJECTS_DIR / slug)

# ── copy bundled templates into ~/.pwnlog/templates, never overwrite ──
def _seed_templates() -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    if not BUNDLED_TEMPLATES.exists():
        return
    for src in BUNDLED_TEMPLATES.glob("*.json"):
        dest = TEMPLATES_DIR / src.name
        if not dest.exists():
            shutil.copy(src, dest)

# ── template loading ──────────────────────────────────────────
def list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return [DEFAULT_TEMPLATE]
    names = sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))
    return names or [DEFAULT_TEMPLATE]

def load_template(name: str) -> dict:
    path = TEMPLATES_DIR / f"{name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_FALLBACK_TEMPLATE)

# ── per-project metadata (which template it was built from) ───
def _meta_path(project_path: Path) -> Path:
    return project_path / ".pwnlog-meta.json"

def _read_meta(project_path: Path) -> dict:
    path = _meta_path(project_path)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}

def _write_meta(project_path: Path, meta: dict) -> None:
    _meta_path(project_path).write_text(json.dumps(meta, indent=2), encoding="utf-8")

def get_project_template_name(project_path: Path) -> str:
    return _read_meta(project_path).get("template", DEFAULT_TEMPLATE)

# ── create a new project ─────────────────────────────────────
def create_project(name: str, template: str = DEFAULT_TEMPLATE) -> Path:
    slug = _slugify(name)
    project_path = PROJECTS_DIR / slug

    if project_path.exists():
        raise FileExistsError(f"Project '{slug}' already exists.")

    project_path.mkdir(parents=True)

    for folder in FOLDERS:
        (project_path / folder).mkdir()

    _write_meta(project_path, {"template": template})
    ensure_recon_tree(project_path)
    _init_journal(project_path, name)
    _init_timeline(project_path, name)
    set_active_project(slug)

    return project_path

# ── create/backfill the recon tree (safe to call repeatedly) ──
# Uses whichever template the project was built from — a project never
# gets silently reshaped just because the default template changed.
def ensure_recon_tree(project_path: Path, template: Optional[str] = None) -> None:
    if not project_path.exists():
        return

    if template is None:
        template = get_project_template_name(project_path)
    tpl = load_template(template)

    for folder in tpl["folders"]:
        (project_path / folder).mkdir(parents=True, exist_ok=True)

    findings_dir = project_path / tpl.get("findings_dir", "05-findings")
    findings_dir.mkdir(parents=True, exist_ok=True)
    template_path = findings_dir / "template.md"
    if not template_path.exists():
        template_path.write_text(tpl.get("finding_template", ""), encoding="utf-8")

    if not _meta_path(project_path).exists():
        _write_meta(project_path, {"template": template})

# ── get (and create) a per-host folder, wherever this template puts them ──
def get_host_dir(project_path: Path, host: str) -> Path:
    tpl = load_template(get_project_template_name(project_path))
    host_dir = project_path / tpl.get("host_dir", "02-hosts") / _sanitize_host(host)
    host_dir.mkdir(parents=True, exist_ok=True)
    return host_dir

def _sanitize_host(host: str) -> str:
    return (
        host.strip()
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace(" ", "_")
    )

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