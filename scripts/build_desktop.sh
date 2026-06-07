#!/usr/bin/env bash
# Build a native one-file VPN-Follower binary for the current OS.
# Usage: scripts/build_desktop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller .

# PyInstaller writes to ./dist relative to the current working directory (repo root).
pyinstaller --clean -y packaging/vpnfollower.spec

echo
echo "Built binary:"
ls -lh dist/vpnfollower* 2>/dev/null || ls -lh dist/
echo
echo "Run it:  ./dist/vpnfollower self"
