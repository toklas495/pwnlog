import argparse
import sys
from pathlib import Path

from core.project import (
    init_pwnlog, list_projects, create_project,
    set_active_project, get_active_project_name,
    PROJECTS_DIR, list_templates, load_template,
    get_project_template_name, DEFAULT_TEMPLATE,
)
from core.importer import import_file
from core.logger import get_entries


def cmd_import(args) -> None:
    project_path = None
    if args.project:
        project_path = PROJECTS_DIR / args.project
        if not project_path.exists():
            print(f"[pwnlog] project '{args.project}' not found.")
            sys.exit(1)

    try:
        dest = import_file(
            src          = Path(args.file),
            project_path = project_path,
            host         = args.host,
            ftype        = args.type,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[pwnlog] {e}")
        sys.exit(1)

    project_name = args.project or get_active_project_name()
    print(f"[pwnlog] imported into '{project_name}' -> {dest}")

    if args.host:
        print(f"[pwnlog] filed under host: {args.host}")
    print("[pwnlog] your next Alt+Shift+Z note will auto-link this file.")


def cmd_projects(args) -> None:
    projects = list_projects()
    active   = get_active_project_name()

    if not projects:
        print("[pwnlog] no projects yet.")
        return

    for p in projects:
        marker = " *" if p == active else "  "
        print(f"{marker} {p}")


def cmd_new_project(args) -> None:
    template = args.template or DEFAULT_TEMPLATE
    if template not in list_templates():
        print(f"[pwnlog] no template named '{template}'. Available: {', '.join(list_templates())}")
        sys.exit(1)
    try:
        path = create_project(args.name, template=template)
        print(f"[pwnlog] created project -> {path}  (template: {template})")
    except FileExistsError as e:
        print(f"[pwnlog] {e}")
        sys.exit(1)


def cmd_templates(args) -> None:
    names = list_templates()
    for name in names:
        tpl = load_template(name)
        desc = tpl.get("description", "")
        print(f"  {name:<12} {desc}")
    print(f"\n[pwnlog] templates live at ~/.pwnlog/templates/*.json — copy one and edit the "
          f"'folders' list to build your own, then use it with: pwnlog new <name> --template <yours>")


def cmd_use(args) -> None:
    if args.name not in list_projects():
        print(f"[pwnlog] project '{args.name}' not found.")
        sys.exit(1)
    set_active_project(args.name)
    print(f"[pwnlog] active project -> {args.name}")


def cmd_show(args) -> None:
    project_path = None
    if args.project:
        project_path = PROJECTS_DIR / args.project
        if not project_path.exists():
            print(f"[pwnlog] project '{args.project}' not found.")
            sys.exit(1)

    entries = get_entries(project_path)
    if args.category:
        entries = [e for e in entries if e["category"].lower() == args.category.lower()]

    if not entries:
        print("[pwnlog] no entries found.")
        return

    entries = entries[-args.n:]
    for e in entries:
        time_str = e["timestamp"][:16].replace("T", " ")
        tag      = e["category"]
        note     = e["note"].splitlines()[0][:90]
        marks    = ""
        if e.get("screenshot"):
            marks += " 📎"
        if e.get("linked_file"):
            marks += " 📄"
        print(f"{time_str}  [{tag}]  {note}{marks}")


def cmd_stats(args) -> None:
    project_name = args.project or get_active_project_name()
    project_path = PROJECTS_DIR / project_name if project_name else None

    if not project_path or not project_path.exists():
        print("[pwnlog] no active project.")
        return

    entries = get_entries(project_path)
    counts: dict = {}
    for e in entries:
        cat = e.get("category", "Note")
        counts[cat] = counts.get(cat, 0) + 1

    print(f"[pwnlog] {project_name} — {len(entries)} entries")
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {cat}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pwnlog",
        description="PwnLog CLI — file tool output into your project's recon tree.",
    )
    sub = parser.add_subparsers(dest="command")

    p_import = sub.add_parser("import", help="Import a file (nmap, subfinder, etc.) into a project")
    p_import.add_argument("file", help="Path to the file to import")
    p_import.add_argument("--project", help="Project slug (defaults to active project)")
    p_import.add_argument("--host", help="Associate this file with a specific host/IP -> 02-hosts/<host>/")
    p_import.add_argument(
        "--type", dest="type",
        choices=["subdomains", "dorks", "github", "asn", "whois",
                 "resolved", "httpx", "endpoints", "js",
                 "directories", "params", "apis"],
        help="File category, used when --host is not given",
    )
    p_import.set_defaults(func=cmd_import)

    p_projects = sub.add_parser("projects", help="List all projects")
    p_projects.set_defaults(func=cmd_projects)

    p_new = sub.add_parser("new", help="Create a new project")
    p_new.add_argument("name")
    p_new.add_argument("--template", help="Directory template to use (default: 'default'). See `pwnlog templates`.")
    p_new.set_defaults(func=cmd_new_project)

    p_templates = sub.add_parser("templates", help="List available directory templates")
    p_templates.set_defaults(func=cmd_templates)

    p_use = sub.add_parser("use", help="Set the active project")
    p_use.add_argument("name")
    p_use.set_defaults(func=cmd_use)

    p_show = sub.add_parser("show", help="Show recent entries in the terminal (no dashboard needed)")
    p_show.add_argument("--project", help="Project slug (defaults to active project)")
    p_show.add_argument("--category", help="Filter by tag/category")
    p_show.add_argument("-n", type=int, default=20, help="How many entries to show (default 20)")
    p_show.set_defaults(func=cmd_show)

    p_stats = sub.add_parser("stats", help="Show entry counts per tag for a project")
    p_stats.add_argument("--project", help="Project slug (defaults to active project)")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    init_pwnlog()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
