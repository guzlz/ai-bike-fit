#!/usr/bin/env bash
# AI Bike Fit - one-command setup for macOS / Linux
#
#   bash setup.sh
#
# Installs uv (if missing), all Python dependencies, and ffmpeg (if missing).
# After this, run:  uv run python analyze_bikefit.py --input my-ride.mov --out out_fit
set -euo pipefail
cd "$(dirname "$0")"

echo "== AI Bike Fit setup =="

# 1. uv (installs and manages Python 3.12 automatically)
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "uv OK"

# 2. Python deps (ultralytics, supervision, opencv, numpy, torch...) from the lockfile
echo "Installing Python dependencies (this pulls PyTorch, ~1-2 min)..."
uv sync
echo "Dependencies OK"

# 3. ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Installing ffmpeg..."
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
  else
    echo "Please install ffmpeg manually: https://ffmpeg.org/download.html"
  fi
fi
echo "ffmpeg OK"

echo
echo "Done. Now run:"
echo "  uv run python analyze_bikefit.py --input my-ride.mov --out out_fit"
