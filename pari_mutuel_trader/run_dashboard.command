#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "[pari_mutuel_trader] First-time setup (creating .venv + installing deps)..."
  make setup
fi

echo "[pari_mutuel_trader] Launching Streamlit dashboard..."
make ui
