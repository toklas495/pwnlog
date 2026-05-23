#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller \
  --name pwnlog \
  --onefile \
  --noconfirm \
  --add-data "assets:assets" \
  main.py

echo "Build complete: dist/pwnlog"
