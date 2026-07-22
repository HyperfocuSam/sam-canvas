#!/usr/bin/env bash
# Start the sam-canvas bridge and open the canvas as a DEDICATED window.
# Idempotent about BOTH the server and the window: if the canvas is already running,
# it does NOT spawn another window (no duplicates on repeated launches).
# Set SAM_CANVAS_FORCE_WINDOW=1 to open a fresh window even when already running.
set -uo pipefail

PORT="${SAM_CANVAS_PORT:-3899}"
DIR="$(cd "$(dirname "$0")" && pwd)"
export SAM_CANVAS_FILE="${SAM_CANVAS_FILE:-$DIR/canvas.excalidraw}"
export SAM_CANVAS_PORT="$PORT"
URL="http://localhost:$PORT"

STARTED=0
if ! curl -s -o /dev/null "$URL/canvas" 2>/dev/null; then
  nohup python3 "$DIR/server.py" > "$DIR/.serve.log" 2>&1 &
  sleep 2
  STARTED=1
fi

if ! curl -s -o /dev/null "$URL/canvas" 2>/dev/null; then
  echo "ERROR: server did not start; see $DIR/.serve.log"
  exit 1
fi

echo "sam-canvas live → $URL"
echo "canvas file: $SAM_CANVAS_FILE"

# Only open a window when we actually started the server (avoids duplicate windows).
if [ "$STARTED" = "0" ] && [ -z "${SAM_CANVAS_FORCE_WINDOW:-}" ]; then
  echo "Already running — its window should be open. If you closed it, open $URL"
  echo "(or re-run with SAM_CANVAS_FORCE_WINDOW=1 to pop a fresh window)."
  exit 0
fi

# Prefer a chromeless Chrome/Chromium "app window" docked to the right half of the
# screen — a dedicated space you can always find. Falls back to a normal browser open.
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null)" \
  "$(command -v chromium 2>/dev/null)" ; do
  [ -n "$c" ] && [ -x "$c" ] && { CHROME="$c"; break; }
done

if [ -n "$CHROME" ]; then
  SW=1440; SH=900
  if command -v osascript >/dev/null 2>&1; then
    read -r SW SH < <(osascript -e 'tell application "Finder" to get {word 3, word 4} of (get bounds of window of desktop)' 2>/dev/null | tr ',' ' ') || true
    SW="${SW:-1440}"; SH="${SH:-900}"
  fi
  HALF=$(( SW / 2 ))
  "$CHROME" --app="$URL" --new-window --window-position="$HALF",0 --window-size="$HALF","$SH" \
    >/dev/null 2>&1 &
  echo "opened as a docked app window (right half); snap it wherever you like."
else
  (open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null) || echo "Open $URL in your browser."
fi
