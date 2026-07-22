#!/usr/bin/env bash
# Start the sam-canvas bridge and show the canvas in ONE dedicated window.
# - If the canvas is already open, it FOCUSES that window (never a duplicate).
# - If it's running but the window was closed, it opens a fresh one.
# Set SAM_CANVAS_FORCE_WINDOW=1 to always pop a new window.
set -uo pipefail

PORT="${SAM_CANVAS_PORT:-3899}"
DIR="$(cd "$(dirname "$0")" && pwd)"
export SAM_CANVAS_FILE="${SAM_CANVAS_FILE:-$DIR/canvas.excalidraw}"
export SAM_CANVAS_PORT="$PORT"
URL="http://localhost:$PORT"

open_window() {
  # A chromeless Chrome/Chromium app window docked to the right half of the screen.
  local chrome=""
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$(command -v google-chrome 2>/dev/null)" \
    "$(command -v chromium 2>/dev/null)" ; do
    [ -n "$c" ] && [ -x "$c" ] && { chrome="$c"; break; }
  done
  if [ -n "$chrome" ]; then
    local sw=1440 sh=900
    if command -v osascript >/dev/null 2>&1; then
      read -r sw sh < <(osascript -e 'tell application "Finder" to get {word 3, word 4} of (get bounds of window of desktop)' 2>/dev/null | tr ',' ' ') || true
      sw="${sw:-1440}"; sh="${sh:-900}"
    fi
    "$chrome" --app="$URL" --new-window --window-position="$(( sw / 2 ))",0 --window-size="$(( sw / 2 ))","$sh" \
      >/dev/null 2>&1 &
    echo "opened a docked canvas window (right half); snap it wherever you like."
  else
    (open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null) || echo "Open $URL in your browser."
  fi
}

focus_existing() {
  # macOS: raise the existing canvas window (Chrome app window or tab) to the front.
  # Prints "true" if it found and focused one.
  command -v osascript >/dev/null 2>&1 || { echo "false"; return; }
  osascript <<APPLESCRIPT 2>/dev/null || echo "false"
tell application "Google Chrome"
  set found to false
  repeat with w in windows
    repeat with t in tabs of w
      if (URL of t) contains "localhost:$PORT" then
        set index of w to 1
        set found to true
        exit repeat
      end if
    end repeat
    if found then exit repeat
  end repeat
  if found then activate
  return (found as string)
end tell
APPLESCRIPT
}

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

if [ "$STARTED" = "1" ] || [ -n "${SAM_CANVAS_FORCE_WINDOW:-}" ]; then
  open_window
elif [ "$(focus_existing)" = "true" ]; then
  echo "brought the existing canvas window to the front."
else
  open_window   # running, but the window was closed — open a fresh one
fi
