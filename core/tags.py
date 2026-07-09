import json
from pathlib import Path
from typing import List

STATE_KEY = "custom_tags"
MAX_TAGS  = 30


def _state_path(project_path: Path) -> Path:
    return project_path / ".pwnlog_state.json"

def _read_state(project_path: Path) -> dict:
    path = _state_path(project_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_state(project_path: Path, state: dict) -> None:
    _state_path(project_path).write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── most-recently-used custom tags for this project ───────────
def get_recent_tags(project_path: Path) -> List[str]:
    return _read_state(project_path).get(STATE_KEY, [])

# ── record a tag was used, most-recent-first, deduped ─────────
def record_tag(project_path: Path, tag: str) -> None:
    tag = tag.strip()
    if not tag:
        return

    state = _read_state(project_path)
    tags  = state.get(STATE_KEY, [])
    tags  = [t for t in tags if t.lower() != tag.lower()]
    tags.insert(0, tag)

    state[STATE_KEY] = tags[:MAX_TAGS]
    _write_state(project_path, state)
