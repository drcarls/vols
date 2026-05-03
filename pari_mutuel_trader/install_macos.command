#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="PariMutuelTrader.app"
DEST_DIR="$HOME/Applications"

mkdir -p "$DEST_DIR"
"$PROJECT_DIR/scripts/build_macos_app.sh"
cp -R "$PROJECT_DIR/dist/$APP_NAME" "$DEST_DIR/$APP_NAME"

echo "Installed: $DEST_DIR/$APP_NAME"
echo "You can now double-click PariMutuelTrader in ~/Applications."
