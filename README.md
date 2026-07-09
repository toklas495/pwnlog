# ⚡ PwnLog

```
██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  ██████╗
██╔══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔════╝
██████╔╝██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║██║  ███╗
██╔═══╝ ██║███╗██║██║╚██╗██║██║     ██║   ██║██║   ██║
██║     ╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝╚██████╔╝
╚═╝      ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝
```

> A frictionless logging tool for bug bounty hunters and pentesters.
> One hotkey captures what you found, right when you found it. Your report writes itself.

---

## Table of contents

- [The problem](#the-problem)
- [How it works](#how-it-works)
- [Install](#install)
- [Running PwnLog](#running-pwnlog)
- [The popup](#the-popup)
- [The CLI](#the-cli)
- [The dashboard](#the-dashboard-optional)
- [Directory templates](#directory-templates)
- [Importing tool output](#importing-tool-output)
- [What gets captured](#what-gets-captured)
- [Data & privacy](#data--privacy)
- [Project layout on disk](#project-layout-on-disk)
- [Stack](#stack)
- [Building a binary](#building-a-binary)
- [Philosophy](#philosophy)
- [License](#license)

---

## The problem

You find something interesting mid-hunt. You think *"I'll note this later."* You never do.

Three days later you're staring at a blank report, trying to remember what that endpoint
was, what parameter you changed, and whether you even have proof.

## How it works

```
Alt + Shift + Z
```

That's it. One popup, anywhere on your screen, over any window. Type what you found,
tag it, hit Enter. Back to hacking in under five seconds.

PwnLog runs quietly in the background and handles the rest: timestamp, active window,
screenshot, a running journal, and a structured recon tree per target — all without
ever pulling focus away from your work until you ask for it.

---

## Install

```bash
git clone https://github.com/you/pwnlog
cd pwnlog
pip install -r requirements.txt
```

**Linux** — install a screenshot helper:

```bash
sudo apt install flameshot xdotool
# or
sudo pacman -S flameshot xdotool
```

**macOS** — screenshots use the built-in `screencapture`, but Flameshot gives you
annotation:

```bash
brew install flameshot
```

**Font** (optional, for the intended look):

```bash
sudo apt install fonts-jetbrains-mono      # ubuntu/debian
sudo pacman -S ttf-jetbrains-mono          # arch
brew install font-jetbrains-mono           # mac
```

---

## Running PwnLog

PwnLog has two faces. Both share the same projects, tags, and hotkey — pick whichever
fits how you work, and switch freely between them.

### Background listener — the default

```bash
python main.py
```

No window, no dock icon, nothing to keep open. It sits invisibly in the background
listening for the hotkey and prints its status to the terminal:

```
[pwnlog] listening — Alt+Shift+Z to log  (project: blinkit)
[pwnlog] ctrl+c to stop. use `python cli.py` to manage projects.
```

Manage everything else — creating projects, switching targets, reviewing entries —
from `cli.py` in another terminal, or a tmux pane, while the listener just runs.

### Visual dashboard — opt-in

```bash
python main.py --dashboard
```

The full dark-mode window: project switcher, live entry feed, tag filters, stats.
The hotkey still works while it's open. Close the dashboard and the listener stops
with it — for an always-on background process, use the default mode instead.

---

## The popup

`Alt + Shift + Z` from anywhere opens it, floating and always-on-top.

| Action | How |
|---|---|
| Focus the note field | happens automatically |
| Save entry | `Enter` |
| Close without saving | `Escape` |
| Pick a fast category | click it, or `Ctrl + 1` – `Ctrl + 0` |
| Use a tag that isn't in the fast grid | type it in the box underneath |
| Reuse a tag you typed before | click its chip under "recent" |
| Attach a screenshot | pick a region, or select `none` to skip |

**Fast categories** (`Ctrl+1`–`Ctrl+0`, muscle memory, unlimited use):

```
Recon → Auth → IDOR → XSS → SQLi → SSRF → LFI → Logic → Dead End → Note
```

**Custom tags** — there's no fixed taxonomy beyond those ten. Type anything —
`CORS`, `Race Condition`, `Prototype Pollution`, whatever the target actually needs —
and it's saved as that entry's category. Every custom tag you use gets remembered
*per project* and shown as a one-click chip the next time you open the popup, so your
tag set grows out of how you actually hunt instead of a taxonomy someone else guessed
at. `pwnlog stats` reports on custom tags the same as the fixed ten.

---

## The CLI

Full project management without ever opening a window:

```bash
python cli.py new <name> [--template <name>]   # create a project
python cli.py use <name>                       # switch active project
python cli.py projects                         # list all projects, * marks active
python cli.py templates                        # list available directory templates

python cli.py show [--project <name>] [--category <tag>] [-n <count>]
python cli.py stats [--project <name>]         # entry counts per tag

python cli.py import <file> [--project <name>] [--host <host>] [--type <type>]
```

**`show`** — recent entries straight in the terminal:

```bash
$ python cli.py show --category idor -n 5
2026-05-22 14:32  [IDOR]  changed user id from 99 to 12, got full victim profile back 📎
2026-05-21 09:10  [IDOR]  order_id enumerable on /api/orders/{id} 📄
```

**`stats`** — a quick per-tag breakdown of a project:

```bash
$ python cli.py stats
[pwnlog] blinkit — 47 entries
    18  Recon
    11  IDOR
     9  Auth
     6  Prototype Pollution
     3  Dead End
```

---

## The dashboard (optional)

`python main.py --dashboard` opens the full window if you want to see things visually:

- **Project switcher** — jump between targets, create new ones (with a template
  picker), delete old ones
- **Live entry feed** — every popup save appears instantly, no refresh needed
- **Tag filters** — grouped in a scrollable sidebar so it stays usable even with
  a large custom-tag set
- **Today's count / totals** — at a glance

---

## Directory templates

Every hunter organizes recon differently, so the folder tree isn't hardcoded — it's a
plain JSON file.

```bash
$ python cli.py templates
  default      Haddix-style recon tree — passive/active recon, per-host discovery,
               vuln-hunting buckets, findings, deadends, report.
  minimal      Bare-bones structure — one recon dump, per-host notes, one findings
               folder. Good starting point to fork your own.
```

Templates live at `~/.pwnlog/templates/*.json`, seeded on first run and never
overwritten after that — edit them freely, they're yours. Format:

```json
{
  "name": "mobile",
  "description": "Mobile pentest layout.",
  "folders": ["static-analysis", "dynamic-analysis", "network-traffic", "findings"],
  "host_dir": "network-traffic",
  "findings_dir": "findings",
  "finding_template": "# Finding\n\n**Severity:**\n**Component:**\n\n## Details\n"
}
```

- `folders` — the tree that gets created under every new project
- `host_dir` — which folder gets a per-host subfolder (used by `--host` on import)
- `findings_dir` / `finding_template` — where the findings write-up template lives

Use it:

```bash
python cli.py new my-target --template mobile
```

A project remembers which template built it (`.pwnlog-meta.json` inside the project
folder), so changing the default template later never reshapes a project you already
started.

> **Note:** `import --type` (see below) files into `01-recon/...`-style paths that
> match the `default` template. On a custom template, prefer `--host` — it always
> resolves correctly via that template's `host_dir` — or pass a path and move the file
> yourself.

---

## Importing tool output

Feed raw tool output straight into the recon tree, and it auto-links to your next
journal entry:

```bash
python cli.py import subdomains.txt --type subdomains
python cli.py import nmap.txt --host 54.169.194.99
```

| `--type` | Lands in (default template) |
|---|---|
| `subdomains` | `01-recon/passive/subdomains` |
| `dorks` | `01-recon/passive/google_dorks` |
| `github` | `01-recon/passive/github_dorks` |
| `asn`, `whois` | `01-recon/passive` |
| `resolved`, `httpx` | `01-recon/active` |
| `endpoints` | `03-discovery/endpoints` |
| `js` | `03-discovery/js_files` |
| `directories` | `03-discovery/directories` |
| `params` | `03-discovery/params` |
| `apis` | `03-discovery/apis` |

Pass `--host <ip-or-domain>` instead of `--type` to file something under that host's
own folder — the next entry you save within 15 minutes auto-links to it.

---

## What gets captured

Every entry automatically records:

```
timestamp     → 2026-05-22 14:32
category      → IDOR
note          → your words exactly
window title  → Firefox — Tesla Admin Panel
screenshot    → optional, annotated via Flameshot
linked file   → optional, if you imported something in the last 15 min
```

Two files build themselves as you go:

**`journal.md`** — human-readable, open it a year from now and understand everything:

```markdown
## 2026-05-22 14:32 — IDOR

> Firefox — Tesla Admin Panel

changed user id from 99 to 12, got full victim profile back.

![screenshot](screenshots/2026-05-22_1432_idor_changed_user_id.png)

---
```

**`timeline.json`** — structured, grep it, parse it, build on it:

```json
{
  "id"           : "20260522143201234",
  "timestamp"    : "2026-05-22T14:32:01",
  "category"     : "IDOR",
  "note"         : "changed user id from 99 to 12, got full victim profile back.",
  "window_title" : "Firefox — Tesla Admin Panel",
  "screenshot"   : "screenshots/2026-05-22_1432_idor.png"
}
```

---

## Data & privacy

```
~/.pwnlog/
├── config.json
├── templates/
│   ├── default.json
│   └── minimal.json
└── projects/
    └── your-target/
        ├── journal.md
        ├── timeline.json
        ├── .pwnlog-meta.json     ← which template built this project
        ├── .pwnlog_state.json    ← recent custom tags for this project
        └── screenshots/
```

Everything stays on your machine. Nothing is transmitted, ever.

## Project layout on disk

A project created with the `default` template:

```
your-target/
├── 01-recon/
│   ├── passive/ {subdomains, google_dorks, github_dorks}
│   └── active/
├── 02-hosts/<host>/
├── 03-discovery/ {endpoints, js_files, directories, params, apis}
├── 04-vuln-hunting/ {auth, idor, xss, sqli, ssrf, lfi, business-logic, misc}
├── 05-findings/ (template.md)
├── 06-deadends/
├── 07-report/
├── screenshots/
├── exports/
├── journal.md
└── timeline.json
```

---

## Stack

```
python          core language
customtkinter   dark native UI (popup + dashboard)
pynput          global hotkey listener
flameshot       annotated screenshots (linux)
screencapture   screenshots (mac)
pyautogui       fallback screenshots
```

---

## Building a binary

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole main.py
./dist/pwnlog
```

---

## Philosophy

> The best documentation tool is the one you actually use.

PwnLog isn't trying to be Burp Suite, and it isn't trying to be Notion. It does one
thing: captures what you found, exactly when you found it, with zero interruption to
your flow. No forced taxonomy, no forced UI, no forced directory structure — the
fixed ten tags and the `default` template are fast starting points, not walls.

Open your journal after a session. Your report is already half written.

---

## License

MIT License

Copyright (c) 2026 toklas495

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

*Built for people who hack, not people who like taking notes.*
