## README.md

```markdown
# ⚡ PwnLog

██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  ██████╗
██╔══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔════╝
██████╔╝██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║██║  ███╗
██╔═══╝ ██║███╗██║██║╚██╗██║██║     ██║   ██║██║   ██║
██║     ╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝╚██████╔╝
╚═╝      ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝

> a dead simple logging tool for bug hunters and pentesters.
> no forms. no friction. one hotkey. your documentation writes itself.

---

## the problem

you find something interesting mid-hunt.
you think *"i'll note this later"*.
you never do.

three days later you're staring at a blank report
trying to remember what that endpoint was,
what parameter you changed,
and whether you even have proof.

---

## the fix

```
ALT + SHIFT + Z
```

one popup. type what you found. hit enter.
back to hacking in under five seconds.

pwnlog handles the rest —
timestamp, window context, screenshot, markdown journal.
everything organized. nothing forgotten.

---

## install

```bash
git clone https://github.com/you/pwnlog
cd pwnlog

pip install -r requirements.txt
```

**linux** — install screenshot helper:

```bash
sudo apt install flameshot xdotool
# or
sudo pacman -S flameshot xdotool
```

**mac**

```bash
brew install flameshot
```

**font** — install JetBrains Mono for best experience:

```bash
# ubuntu/debian
sudo apt install fonts-jetbrains-mono

# arch
sudo pacman -S ttf-jetbrains-mono

# mac
brew install font-jetbrains-mono
```

---

## run

```bash
python main.py
```

---

## usage

| action | how |
|---|---|
| open log popup | `ALT + SHIFT + Z` from anywhere |
| save entry | `Enter` |
| close without saving | `Escape` |
| cycle categories | `Tab` |
| skip screenshot | select `none` in popup |

---

## what gets captured

every entry automatically records:

```
timestamp       → 2026-05-22 14:32
category        → IDOR
note            → your words exactly
window title    → Firefox — Tesla Admin Panel
screenshot      → optional, annotated via flameshot
```

---

## output

every project generates two files that build themselves:

**journal.md** — human readable, open after a year and understand everything

```markdown
## 2026-05-22 14:32 — IDOR

> Firefox — Tesla Admin Panel

changed user id from 99 to 12, got full victim profile back.

![screenshot](screenshots/2026-05-22_1432_idor_changed_user_id.png)

---
```

**timeline.json** — structured, grep it, parse it, build on it

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

## categories

```
Recon  →  Auth  →  IDOR  →  XSS  →  SQLi
SSRF   →  LFI   →  Logic →  Dead End  →  Note
```

---

## data

```
~/.pwnlog/
├── config.json
└── projects/
    └── your-target/
        ├── journal.md
        ├── timeline.json
        └── screenshots/
```

everything stays on your machine.
nothing is transmitted. ever.

---

## stack

```
python          core language
customtkinter   dark native UI
pynput          global hotkey listener
flameshot       annotated screenshots (linux)
screencapture   screenshots (mac)
pyautogui       fallback screenshots
```

---

## build binary

**linux**

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole main.py
./dist/pwnlog
```

---

## categories explained

| tag | use when |
|---|---|
| `Recon` | gathering info, subdomains, endpoints |
| `Auth` | login, session, token, cookie issues |
| `IDOR` | accessing other users data |
| `XSS` | script injection, reflected, stored, dom |
| `SQLi` | database injection |
| `SSRF` | server side request forgery |
| `LFI` | local file inclusion |
| `Logic` | business logic flaws |
| `Dead End` | tried, confirmed not vulnerable |
| `Note` | anything else, thoughts, observations |

---

## philosophy

> the best documentation tool is the one you actually use.

pwnlog is not trying to be burp suite.
it is not trying to be notion.
it does one thing — captures what you found
exactly when you found it
with zero interruption to your flow.

open your journal after a session.
your report is already half written.

---

## license

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

*built for people who hack, not people who like taking notes.*
```
