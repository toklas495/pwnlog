#!/usr/bin/env bash
set -euo pipefail

if ! command -v flameshot >/dev/null 2>&1; then
  if [[ -f /etc/debian_version ]]; then
    sudo apt update
    sudo apt install -y flameshot
    exit 0
  fi

  if [[ -f /etc/fedora-release ]] || [[ -f /etc/redhat-release ]]; then
    sudo dnf install -y flameshot
    exit 0
  fi

  if [[ -f /etc/arch-release ]]; then
    sudo pacman -S --noconfirm flameshot
    exit 0
  fi

  echo "Unsupported distro. Please install flameshot manually."
  exit 1
fi

echo "flameshot is already installed."
