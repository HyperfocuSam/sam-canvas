#!/usr/bin/env bash
# Start the sam-canvas bridge and open the canvas as a DEDICATED window.
# Idempotent: reuses the running server if the port is already up.
set -uo pipefail

PORT="${SAM_CANVAS_PORT:-3899}"
DIR="$(cd "$(dirname "$0")" && pwd)"
export SAM_CANVAS_FILE="${SAM_CANVAS_FILE:-$DIR/canvas.excalidraw}"
export SAM_CANVAS_PORT="$PORT"
URL="http://localhost:$PORT"

if ! curl -s -o /dev/null "$URL/canvas" 2>/dev/null; then
  nohup python3 "$DIR/server.py" > "$DIR/.serve.log" 2>&1 &
  sleep 2
fi

if ! curl -s -o /dev/null "$URL/canvas" 2>/dev/null; then
  echo "ERROR: server did not start; see $DIR/.serve.log"
  exit 1
fi

echo "sam-canvas live → $URL"
echo "canvas file: $SAM_CANVAS_FILE"

# Prefer a chromeless Chrome/Chromium "app window" docked to the right half of the
# screen — a dedicated space you can always find (no tab hunting). Falls back to a
# normal browser open on any platform.
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
