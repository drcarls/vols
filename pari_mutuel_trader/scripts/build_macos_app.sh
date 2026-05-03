#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="PariMutuelTrader"
DIST_DIR="$PROJECT_DIR/dist"
APP_PATH="$DIST_DIR/${APP_NAME}.app"
LAUNCHER="$PROJECT_DIR/run_dashboard.command"

if ! command -v osacompile >/dev/null 2>&1; then
  echo "osacompile not found. This script must run on macOS." >&2
  exit 1
fi

mkdir -p "$DIST_DIR"
TMP_AS="$DIST_DIR/${APP_NAME}.applescript"

cat > "$TMP_AS" <<EOF
on run
    do shell script "open -a Terminal " & quoted form of POSIX path of "$LAUNCHER"
end run
EOF

rm -rf "$APP_PATH"
osacompile -o "$APP_PATH" "$TMP_AS"
rm -f "$TMP_AS"

echo "Built app: $APP_PATH"
